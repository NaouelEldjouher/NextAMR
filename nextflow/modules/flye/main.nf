process FLYE {
    tag "$meta.id"
    
    // StaphB maintains a very reliable Flye image
    container 'staphb/flye:2.9.3'

    // Automatically save your final assemblies to your output folder
    publishDir "${params.outdir}/flye", mode: 'copy', pattern: '*.fasta'

    input:
    tuple val(meta), path(longreads)

    output:
    // Change this from 'emit: fasta' to 'emit: assembly'
    tuple val(meta), path("${meta.id}_flye.fasta"), emit: assembly 
    path "flye.log"                               , emit: log
    path "versions.yml"                           , emit: versions

    script:
    """
    # Run Flye assembly using the long reads
    flye \\
        --nano-hq $longreads \\
        --out-dir ./ \\
        --threads $task.cpus

    # Rename the generic 'assembly.fasta' to include your sample ID
    mv assembly.fasta ${meta.id}_flye.fasta

    # Capture tool version
    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        flye: \$(flye --version)
    END_VERSIONS
    """
}