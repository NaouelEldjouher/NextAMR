process FLYE {
    tag "$meta.id"
    




    publishDir "${params.outdir}/flye", mode: 'copy', pattern: '*.fasta'

    input:
    tuple val(meta), path(longreads)

    output:
   
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

  
    mv assembly.fasta ${meta.id}_flye.fasta

    # Capture tool version
    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        flye: \$(flye --version)
    END_VERSIONS
    """
}