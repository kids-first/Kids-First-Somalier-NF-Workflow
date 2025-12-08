#!/usr/bin/env nextflow

include { EXTRACT } from './modules/local/somalier/extract.nf'
include { RELATE } from './modules/local/somalier/relate.nf'
include { RESULT_INTERPRET } from './modules/local/python/somalier_result_interpretation.nf'
include { TAR_GZ } from './modules/local/ubuntu/tar.nf'

def validate_inputs(param_obj){
    if (params.extract_only){
        println("extract_only flag give, will skip RELATE step")
    }
    def non_empty_param_keys = param_obj.findAll { _key, value -> 
    value != null && value != ""
    }.keySet()
    println(non_empty_param_keys)
    if (param_obj.alignment_file){
        def required_options = [ 'alignment_index', 'fasta', 'fai', 'sites' ]
        def missing = required_options.findAll { param ->  !non_empty_param_keys.contains(param) }
        if (missing){
            error "When providing 'alignment_file', you must also provide '${required_options}'. You are missing $missing" 
        }
    }
}

workflow {
    main:
    validate_inputs(params)
    // extract
    alignment_file = params.alignment_file ? channel.fromPath(params.alignment_file) : channel.empty() // BAM/CRAM file if somalier binary not available
    alignment_index = params.alignment_index ? channel.fromPath(params.alignment_index) : channel.empty() // BAM/CRAM index if somalier binary not available
    fasta = params.fasta ? channel.fromPath(params.fasta) : channel.value([]) // extract requires fasta
    fai = params.fai ? channel.fromPath(params.fai) : channel.value([]) // extract requires fai
    sites = params.sites ? channel.fromPath(params.sites).collect() : channel.value([]) // extract requires sites
    extract_sample_id = params.extract_sample_id ? channel.fromList(params.extract_sample_id) : channel.value([]) // optional to rename extract inputs
    // relate
    somalier_binary = params.somalier_binary ? channel.fromPath(params.somalier_binary) : channel.value([]) // Use if extract already previously run
    groups_csv = params.groups_csv ? channel.fromPath(params.groups_csv) : channel.value([])
    ped = params.ped ? channel.fromPath(params.ped) : channel.value([])

    align_index = alignment_file.merge(alignment_index)
    fasta_fai = fasta.merge(fai).collect()
    EXTRACT(
            align_index,
            fasta_fai,
            sites,
            extract_sample_id
        )
    if(!params.extract_only){
        somalier_binary = EXTRACT.out.concat(somalier_binary).collect()
        RELATE(
            somalier_binary,
            groups_csv,
            ped
        )
    }
    RESULT_INTERPRET(
        ped,
        RELATE.out.samples_tsv,
        groups_csv,
        RELATE.out.groups_tsv
    ) | TAR_GZ
}