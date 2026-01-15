process RESULT_INTERPRET {
    label 'C2'
    container "python:3.12.12"

    input:
    path(ped)
    path(samples_tsv)
    path(groups_csv)
    path(groups_tsv)

    output:
    path('*.somalier_interpretation.tsv'), emit: somalier_interpretation_tsv
    stdout emit: interpret_status

    script:
    def relate_params = ped ? "--ped $ped --samples-tsv $samples_tsv" : ''
    def swap_params = groups_csv ? "--groups-csv $groups_csv --groups-tsv $groups_tsv" : ''
    def interpret_ext_args = task.ext.args ?: ''
    """
    interpret_somalier.py \\
    $relate_params \\
    $swap_params \\
    $interpret_ext_args
    """
}