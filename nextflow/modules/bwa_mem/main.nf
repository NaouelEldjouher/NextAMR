process BWA_MEM {
    tag "$meta.id"
    container 'staphb/bwa:0.7.17'

    input:
    tuple val(meta), path(assembly), path(reads)

    output:
    tuple val(meta), path(assembly), path("*.sam"), emit: aligned_data

    script:
    """
    bwa index $assembly
    # Added your -a flag! This is vital for Polypolish.
    bwa mem -t $task.cpus -a $assembly ${reads[0]} > alignments_1.sam
    bwa mem -t $task.cpus -a $assembly ${reads[1]} > alignments_2.sam
    """
}