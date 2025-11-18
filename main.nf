#!/usr/bin/env nextflow

include { EXTRACT } from './modules/local/somalier/extract.nf'
include { RELATE } from './modules/local/somalier/relate.nf'

workflow {
    main:
    // extract
    alignment_file = params.alignment_file ? Channel.fromPath(params.alignment_file) : Channel.empty() // BAM/CRAM file if somalier binary not available
    alignment_index = params.alignment_index ? Channel.fromPath(params.alignment_index) : Channel.empty() // BAM/CRAM index if somalier binary not available
    fasta = params.fasta ? Channel.fromPath(params.fasta) : Channel.value([]) // extract requires fasta
    fai = params.fai ? Channel.fromPath(params.fai) : Channel.value([]) // extract requires fai
    sites = params.sites ? Channel.fromPath(params.sites).collect() : Channel.value([]) // extract requires sites
    extract_sample_id = params.extract_sample_id ? Channel.fromList(params.extract_sample_id) : Channel.value([]) // optional to rename extract inputs
    // relate
    somalier_binary = params.somalier_binary ? Channel.fromPath(params.somalier_binary) : Channel.value([]) // Use if extract already previously run
    groups_tsv = params.groups_tsv ? Channel.fromPath(params.groups_tsv) : Channel.value([])
    ped = params.ped ? Channel.fromPath(params.ped) : Channel.value([])

    align_index = extract_sample_id.merge(alignment_file).merge(alignment_index)
    fasta_fai = fasta.merge(fai).collect()
    align_index.view()
    EXTRACT(
            align_index,
            fasta_fai,
            sites
        )
    somalier_binary = EXTRACT.out.concat(somalier_binary).collect()
    somalier_binary.view()
    RELATE(
        somalier_binary,
        groups_tsv,
        ped
    )
}