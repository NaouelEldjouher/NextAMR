process FASTP {
    tag "$meta.id"
    container 'biocontainers/fastp:0.23.4--h5f7e573_0'
    // ADD THIS LINE HERE:
    publishDir "${params.outdir}/fastp", mode: 'copy', pattern: '*.{html,json,fastq.gz}'
    input:
    tuple val(meta), path(reads)

    output:
    tuple val(meta), path("*.fastp.fastq.gz"), emit: reads
    tuple val(meta), path("*.json")           , emit: json
    path "versions.yml"                       , emit: versions

   script:
    def prefix = "${meta.id}"
    // Check if we have two files (paired-end) or one (single-end)
    if (reads instanceof List && reads.size() == 2) {
        """
        fastp \\
            --in1 ${reads[0]} \\
            --in2 ${reads[1]} \\
            --out1 ${prefix}_1.fastp.fastq.gz \\
            --out2 ${prefix}_2.fastp.fastq.gz \\
            --json ${prefix}.fastp.json \\
            --thread $task.cpus

        cat <<-END_VERSIONS > versions.yml
        "${task.process}":
            fastp: \$(fastp --version 2>&1 | sed -e "s/fastp //g")
        END_VERSIONS
        """
    } else {
        """
        fastp \\
            --in1 ${reads} \\
            --out1 ${prefix}.fastp.fastq.gz \\
            --json ${prefix}.fastp.json \\
            --thread $task.cpus

        cat <<-END_VERSIONS > versions.yml
        "${task.process}":
            fastp: \$(fastp --version 2>&1 | sed -e "s/fastp //g")
        END_VERSIONS
        """
    }
}
