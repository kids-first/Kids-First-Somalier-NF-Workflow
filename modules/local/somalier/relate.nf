process RELATE {
    label 'C2'
    container "brentp/somalier:v0.3.1"

    input:
    path(somalier_file)
    path(groups_tsv) 
    path(ped)

    output:
    path('*groups.tsv'), emit: groups_tsv
    path('*html'), emit: interactive_html
    path('*pairs.tsv'), emit: pairs_tsv
    path('*samples.tsv'), emit: samples_tsv

    script:
    def somalier_ext_args = task.ext.args ?: ''
    def input_file_args = groups_tsv ? "--groups $groups_tsv" : ''
    input_file_args += ped ? " --ped $ped" : ''

    """
    somalier relate \\
    $input_file_args \\
    $somalier_ext_args \\
    $somalier_file
    """

}