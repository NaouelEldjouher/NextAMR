process UNICYCLER {
    tag "$meta.id"
    container 'staphb/unicycler:0.5.0'
    
    // 1. Save the finished genome to your results folder
    publishDir "${params.outdir}/unicycler", mode: 'copy'

    input:
    tuple val(meta), path(shortreads), path(longreads)

    output:
    tuple val(meta), path("*.assembly.fasta"), emit: scaf
    path "versions.yml"                      , emit: versions

    script:
    def prefix = "${meta.id}"
    // Handle Long Reads (checks if the file exists and isn't a dummy)
    def long_reads_arg = (longreads && longreads.exists() && longreads.size() > 0) ? "-l $longreads" : ""
    
    // Optimized parameters for your 32GB RAM workstation
    // We skip k=15 and give SPAdes 20GB of memory room
    def unicycler_params = "--mode conservative --kmers 29,41,55,69 --spades_options \"-m 20\""

    if (shortreads instanceof List && shortreads.size() == 2) {
        """
        # Clean up old data to prevent folder conflicts
        rm -rf unicycler_output

        unicycler \\
            -1 ${shortreads[0]} \\
            -2 ${shortreads[1]} \\
            $long_reads_arg \\
            -o unicycler_output \\
            -t $task.cpus \\
            $unicycler_params

        if [ -f unicycler_output/assembly.fasta ]; then
            mv unicycler_output/assembly.fasta ${prefix}.assembly.fasta
        fi

        cat <<-END_VERSIONS > versions.yml
        "${task.process}":
            unicycler: \$(unicycler --version | sed 's/Unicycler v//')
        END_VERSIONS
        """
    } else {
        """
        # Clean up old data
        rm -rf unicycler_output

        unicycler \\
            -s ${shortreads} \\
            $long_reads_arg \\
            -o unicycler_output \\
            -t $task.cpus \\
            $unicycler_params

        if [ -f unicycler_output/assembly.fasta ]; then
            mv unicycler_output/assembly.fasta ${prefix}.assembly.fasta
        fi

        cat <<-END_VERSIONS > versions.yml
        "${task.process}":
            unicycler: \$(unicycler --version | sed 's/Unicycler v//')
        END_VERSIONS
        """
    }
}