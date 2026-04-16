process FILTLONG {
    tag "$meta.id"
  

    input:
    
    tuple val(meta), path(shortreads), path(longreads)

    output:
    tuple val(meta), path("*.filt.fastq.gz"), emit: reads
    path "versions.yml"                     , emit: versions

    script:
    def prefix = "${meta.id}"
   
    def short_args = shortreads ? "-1 ${shortreads[0]} -2 ${shortreads[1]}" : ""
    
    """
    
    filtlong \\
        $short_args \\
        --min_length 500 \\
        --keep_percent 90 \\
        $longreads \\
        | gzip > ${prefix}.filt.fastq.gz

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        filtlong: \$(filtlong --version | sed 's/Filtlong v//')
    END_VERSIONS
    """
}
