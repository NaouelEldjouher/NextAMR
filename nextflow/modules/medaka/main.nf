process MEDAKA {
    tag "$meta.id"
    
    container 'quay.io/biocontainers/medaka:1.11.3--py39h05d5c5e_0'

    input:
    tuple val(meta), path(assembly), path(longreads)

    output:
    tuple val(meta), path("*.polished.fasta"), emit: assembly
    path "versions.yml"                      , emit: versions

    script:
    def prefix = "${meta.id}"
    """
    # FIX: Point the home directory to the current Nextflow work folder 
    # so Medaka has permission to download and save the missing model.
    export HOME=\$(pwd)

    medaka_consensus -i $longreads -d $assembly -o ./ -t $task.cpus -m r1041_e82_400bps_sup_v4.2.0
    
    # Rename output
    mv consensus.fasta ${prefix}.polished.fasta

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        medaka: \$(medaka --version | sed 's/medaka //')
    END_VERSIONS
    """
}
