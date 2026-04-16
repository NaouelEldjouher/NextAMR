process POLYPOLISH {
    tag "$meta.id"


    publishDir "${params.outdir}/polypolish", mode: 'copy', pattern: '*.fasta'

    input:
    
    tuple val(meta), path(assembly), path(sams)

    output:
    tuple val(meta), path("${meta.id}_polypolish.fasta"), emit: assembly
    path "versions.yml"                                 , emit: versions

    script:
    """
   
    polypolish polish $assembly ${sams[0]} ${sams[1]} > ${meta.id}_polypolish.fasta

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        polypolish: \$(polypolish --version 2>&1 | sed 's/Polypolish v//')
    END_VERSIONS
    """
}