process RELATE {
    label 'C2'
    container "brentp/somalier:v0.3.1"

    input:
    path(somalier_file)
    path(groups_csv) 
    path(ped)

    output:
    path('*groups.tsv'), emit: groups_tsv
    path('*samples.tsv'), emit: samples_tsv
    path('*'), emit: all_outputs

    script:
    def somalier_ext_args = task.ext.args ?: ''
    def input_file_args = groups_csv ? "--groups $groups_csv" : ''
    input_file_args += ped ? " --ped $ped" : ''

    """
    somalier relate \\
    $input_file_args \\
    $somalier_ext_args \\
    $somalier_file
    """

}