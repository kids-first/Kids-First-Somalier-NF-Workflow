# Kids First DRC Somalier QC
Somalier ([git repo](https://github.com/brentp/somalier/tree/v0.3.1), [publication](https://pmc.ncbi.nlm.nih.gov/articles/PMC7362544/)) is a sample-swap and relatedness checker.
Here, we have constructed a nextflow workflow to fit our needs for trio-based relatedness QC as well as patient-level QC from cancer-related sequencing.


<p align="center">
  <img src="docs/logo/kids_first_logo.svg" alt="Kids First repository logo" width="660px" />
</p>
<p align="center">
  <a href="https://github.com/kids-first/Kids-First-Somalier-NF-Workflow/blob/main/LICENSE"><img src="https://img.shields.io/github/license/kids-first/Kids-First-Somalier-NF-Workflow.svg?style=for-the-badge"></a>
</p>

## Overview
The workflow is designed to run `extract` to create the somalier extracted sites file if needed (from alignment), then run `relate` to get various relatedness, sex, and sample-swap QC metrics.
Having the workflow runs `extract` + `relate` requires that _all input alignment files be aligned to the same reference_.
Otherwise, `extract` should be run separately.
The `.somalier` formatted files can be provided directly as well, and are worth keeping as they are fairly small and can be used for future comparisons and ancestry predictions (not in this workflow).
Below, some common intended usage scenarios are laid out

## Relatedness check
Most commonly used for trios, can be expanded to include siblings.

### All samples have extracted site files
#### Required
- `somalier_binary`: List of previously created somalier extracted sites files. Should have extension `.somalier`
#### `relate` Recommended
- `ped`: Pedigree file, Described [here](https://gatk.broadinstitute.org/hc/en-us/articles/360035531972-PED-Pedigree-format)
- `infer` Flag to infer relationships as a check/correction if different from input
- `output_prefix`: Set file name prefix. Default is `somalier.`
#### `relate` Optional
- `min_depth`: only genotype sites with at least this depth. Default 7
- `min_ab`: hets sites must be between min-ab and 1 - min_ab. set this to 0.2 for RNA-Seq data (default: 0.3)
- `unknown`: set unknown genotypes to hom-ref
### None or some have extracted site files
For those missing `.somalier` files, if all have the same reference genome
#### `extract` Required
- `alignment_file`: List of alignment files to create somalier binaries
- `alignment_index`: List of alignment file indices to create somalier binaries
- `fasta`: FASTA reference genome
- `fai` FASTA Index
- `sites`: Path to sites somalier sites VCF file. Prebuilt accessible from somalier repo
#### `extract` Optional
- `extract_sample_id`: If desired sample ID is different from `SM` in alignment read group, provide here as a list for _all_
- `extract_sample_prefix`: Prefix existing samples IDs. Could be useful to tag all with a family ID?
### You have mixed reference genomes, or just want somalier site files, no checks
For each set of alignment inputs with the same genome reference, you need at least all from [`extract` Required](#extract-required) and:
- `extract_only`: true

## Sample swap check
Most commonly in the tumor-normal realm for DNA and RNA samples. If none or some have extracted sites, follow the guidelines from [here](#none-or-some-have-extracted-site-files)
### All samples have extracted site files
#### Required
- `somalier_binary`: List of previously created somalier extracted sites files. Should have extension `.somalier`
#### `relate` Recommended
- `groups_csv`: somalier relate optional path to expected groups of samples (e.g. tumor normal pairs). A group file is specified as comma-separated groups per line
- `output_prefix`: Set file name prefix. Default is `somalier.`

## Outputs
### `extract`
- `*.somalier`: List of extracted sites files. Necessary/recommended for repeated analyses using the somalier suite
### `relate`
- `.html`: interactive html with various QA metrics plots
- `.samples.tsv`: .ped like file with extra QC columns
- `.pairs.tsv`: shows IBS (identity by state) for all possible sample pairs
- `.groups.tsv`: shows pairs of samples above a certain relatedness
### `result interpret`
Custom script is run to summarize if errors were found in relationship and/or sex (based on ped input) or if samples swaps found (based on group input).
For each situation, if no issues are found, no file is generated.
- `.somalier_relation_errors.tsv`: has any issues by sample in relationship or sex found
- `.somalier_sample_swap_errors.tsv`: Compared to input groups, outputs which samples failed to match