process BWA_MEM {
    tag "$meta.id"


    input:
    tuple val(meta), path(assembly), path(reads)

    output:
    tuple val(meta), path(assembly), path("*.sam"), emit: aligned_data

    script:
    """
    bwa index $assembly
    
    bwa mem -t $task.cpus -a $assembly ${reads[0]} > alignments_1.sam
    bwa mem -t $task.cpus -a $assembly ${reads[1]} > alignments_2.sam
    """
}