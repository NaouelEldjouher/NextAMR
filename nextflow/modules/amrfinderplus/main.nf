process AMRFINDERPLUS {
    tag "$meta.id"
   

    // 1. Add PublishDir to save the AMR resistance reports
    publishDir "${params.outdir}/amrfinderplus", mode: 'copy'

    input:
    tuple val(meta), path(fasta)

    output:
    tuple val(meta), path("*.tsv"), emit: report
    path "versions.yml"           , emit: versions

    script:
    def prefix = "${meta.id}"
    """
    
    amrfinder \\
        -n $fasta \\
        --threads $task.cpus \\
        --plus \\
        -o ${prefix}_amr.tsv

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        amrfinderplus: \$(amrfinder --version)
    END_VERSIONS
    """
}