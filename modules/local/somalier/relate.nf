process RELATE {
    label 'C2'
    container "brentp/somalier:v0.3.1"

    input:
    path(somalier_file)    

    output:
    path('*groups.tsv'), emit: groups_tsv
    path('*html'), emit: interactive_html
    path('*pars.tsv'), emit: pairs_tsv
    path('*samples.tsv'), emit: samples_tsv

    script:
    def somalier_ext_args = task.ext.args ?: ''
    """
    somalier relate \\
    $somalier_ext_args \\
    $somalier_file
    """

}