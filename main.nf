#!/usr/bin/env nextflow

include { EXTRACT } from './modules/local/somalier/extract.nf'
include { RELATE } from './modules/local/somalier/relate.nf'

workflow {
    main:
    alignment_file = params.alignment_file ? Channel.fromPath(params.alignment_file) : Channel.value([]) // BAM/CRAM file if somalier binary not available
    somalier_binary = params.somalier_binary ? Channel.value(params.somalier_binary) : Channel.value([]) // Use if extract already previously run
    fasta = params.fasta ? Channel.fromPath(params.fasta) : Channel.value([]) // extract requires fasta
    sites = params.sites ? Channel.fromPath(params.sites) : Channel.value([]) // extract requires sites
    extract_sample_id = params.extract_sample_id ? Channel.value(params.extract_sample_id) : Channel.value([]) // optional to rename extract inputs

    if (params.alignment_file){
        somalier_files = EXTRACT(
            alignment_file: alignment_file,
            fasta: fasta,
            sites: sites,
            extract_sample_id: extract_sample_id
        )
    }
    somalier_binary.concat(somalier_files)
    RELATE(
        somalier_file: somalier_binary
    )
}