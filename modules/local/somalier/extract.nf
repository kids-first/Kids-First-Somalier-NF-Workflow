process EXTRACT {
    label 'C2'
    container "brentp/somalier:v0.3.1"

    input:
    path(alignment_file)
    path(fasta)
    path(sites)
    path(extract_sample_id)

    output:
    path('*somalier')

    script:
    def extract_sample_cmd = extract_sample_id ? "export SOMALIER_SAMPLE_NAME=${extract_sample_id}; " : ''
    def extract_sample_prefix = task.ext.extract_sample_prefix ?: ''
    """
    $extract_sample_cmd
    somalier extract \\
    --fasta $fasta \\
    --sites $sites
    $extract_sample_prefix \\
    $alignment_file
    """

}