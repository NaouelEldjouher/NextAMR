#!/usr/bin/env nextflow
nextflow.enable.dsl=2

// --- 1. MODULE IMPORTS ---
include { FASTP as FASTP_HYB }         from './modules/fastp/main'
include { FASTP as FASTP_ILL }         from './modules/fastp/main'
include { SUBSAMPLE as SUB_HYB }       from './modules/subsample'
include { SUBSAMPLE as SUB_ILL }       from './modules/subsample'


include { FILTLONG as FILT_HYB }       from './modules/filtlong/main'
include { FILTLONG as FILT_LR }        from './modules/filtlong/main'

include { UNICYCLER as UNICYCLER_HYB } from './modules/unicycler/main'
include { UNICYCLER as UNICYCLER_ILL } from './modules/unicycler/main'


include { FLYE }                       from './modules/flye'

include { MEDAKA as MEDAKA_HYB }       from './modules/medaka/main'
include { MEDAKA as MEDAKA_LR }        from './modules/medaka/main'

include { AMRFINDERPLUS }              from './modules/amrfinderplus/main'
include { BAKTA }                      from './modules/bakta'

include { BWA_MEM }                    from './modules/bwa_mem'      
include { POLYPOLISH }                 from './modules/polypolish'
include { PYPOLCA }                    from './modules/pypolca'

include { DNAAPLER as DNAAPLER_HYB }   from './modules/dnaapler'
include { DNAAPLER as DNAAPLER_ILL }   from './modules/dnaapler'
include { DNAAPLER as DNAAPLER_LR }    from './modules/dnaapler'

workflow {
    
    // --- 2. INPUT CHANNEL ---
    ch_input = Channel.fromPath(params.input)
        .splitCsv(header:true, sep: (params.input.endsWith('.tsv') ? '\t' : ',')) 
        .map { row -> 
            def type_val = row.type?.toLowerCase()?.trim() ?: "illumina" 
            def meta = [ id: row.sample, type: type_val ]
            
            def r1 = row.fastq_1 ? file(row.fastq_1) : []
            def r2 = row.fastq_2 ? file(row.fastq_2) : []
            def lr = row.longreads ? file(row.longreads) : []
            
            return [ meta, [r1, r2], lr ]
        }

    // --- 3. DYNAMIC BRANCHING ---
    // Updated to handle 'longread' type from your TSV
    ch_input.branch {
        hybrid:   it[0].type == 'hybrid'
        illumina: it[0].type == 'illumina'
        longread: it[0].type == 'long'
    }.set { ch_data }

    // --- 4. LANE A: HYBRID WORKFLOW ---
    FASTP_HYB ( ch_data.hybrid.map { meta, reads, lr -> [ meta, reads ] } )
    ch_filtlong_hyb_in = FASTP_HYB.out.reads.join( ch_data.hybrid.map { meta, reads, lr -> [ meta, lr ] } )
    FILT_HYB ( ch_filtlong_hyb_in )
    SUB_HYB ( FASTP_HYB.out.reads ) 
    ch_unicycler_hyb_input = SUB_HYB.out.reads.join(FILT_HYB.out.reads)
    UNICYCLER_HYB ( ch_unicycler_hyb_input )

    // --- 5. LANE B: ILLUMINA WORKFLOW ---
    FASTP_ILL ( ch_data.illumina.map { meta, reads, lr -> [ meta, reads ] } )
    SUB_ILL ( FASTP_ILL.out.reads )
    ch_unicycler_ill_input = SUB_ILL.out.reads.map { meta, reads -> [ meta, reads, [] ] }
    UNICYCLER_ILL ( ch_unicycler_ill_input )
    DNAAPLER_ILL ( UNICYCLER_ILL.out.scaf )

    // --- 6. NEW LANE C: LONG-READ ONLY WORKFLOW ---
    // 6a. Filter Long Reads (no short-read reference needed)
    FILT_LR ( ch_data.longread.map { meta, reads, lr -> [ meta, [], lr ] } )
    
    // 6b. De Novo Assembly with Flye
    FLYE ( FILT_LR.out.reads )

    // 6c. Polishing with Medaka
    ch_medaka_lr_in = FLYE.out.assembly.join( FILT_LR.out.reads )
    MEDAKA_LR ( ch_medaka_lr_in )

    // 6d. Orientation with Dnaapler
    DNAAPLER_LR ( MEDAKA_LR.out.assembly )


    // --- 7. THE POLISHING CHAIN (HYBRID ONLY) ---
    MEDAKA_HYB ( UNICYCLER_HYB.out.scaf.join(FILT_HYB.out.reads) )
    ch_bwa_input = MEDAKA_HYB.out.assembly.join( FASTP_HYB.out.reads )
    BWA_MEM ( ch_bwa_input )
    POLYPOLISH ( BWA_MEM.out.aligned_data )
    ch_pypolca_input = POLYPOLISH.out.assembly.join( FASTP_HYB.out.reads )
    PYPOLCA ( ch_pypolca_input )
    DNAAPLER_HYB ( PYPOLCA.out.assembly )


    // --- 8. THE MERGE & ANNOTATION ---
    // Merge final oriented assemblies from all three potential lanes
    ch_final_assemblies = DNAAPLER_HYB.out.assembly
        .mix( DNAAPLER_ILL.out.assembly )
        .mix( DNAAPLER_LR.out.assembly )

    BAKTA ( ch_final_assemblies, file(params.bakta_db) )
    AMRFINDERPLUS ( ch_final_assemblies )
}