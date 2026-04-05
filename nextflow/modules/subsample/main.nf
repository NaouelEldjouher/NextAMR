process SUBSAMPLE {
    tag "$meta.id"
    container 'quay.io/biocontainers/seqtk:1.4--he4a0461_2'
    
    // 1. Add the PublishDir to save the downsampled reads
    publishDir "${params.outdir}/subsampled", mode: 'copy', pattern: "*.sub.fastq.gz"

    input:
    tuple val(meta), path(reads)

    output:
    tuple val(meta), path("*.sub.fastq.gz"), emit: reads

    script:
    def prefix = "${meta.id}"
    // 2. Check if we have a pair [R1, R2] or a single file
    if (reads instanceof List && reads.size() == 2) {
        """
        # Process Paired-End: 5M reads from R1 and 5M from R2
        seqtk sample -s100 ${reads[0]} 5000000 | gzip > ${prefix}_1.sub.fastq.gz
        seqtk sample -s100 ${reads[1]} 5000000 | gzip > ${prefix}_2.sub.fastq.gz
        """
    } else {
        """
        # Process Single-End: 5M reads from the only file provided
        seqtk sample -s100 ${reads} 5000000 | gzip > ${prefix}.sub.fastq.gz
        """
    }
}