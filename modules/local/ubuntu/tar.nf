process TAR_GZ {
    label 'C2'
    container 'ubuntu:24.04'

    input:
    path(input_files)

    output:
    path('*tar.gz')

    script:
    """
    tar -czf \\
    ${task.ext.tar_prefix}.tar.gz $input_files
    """

}