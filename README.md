# Kids First DRC Somalier QC
Somalier ([git repo](https://github.com/brentp/somalier/tree/v0.3.3), [publication](https://pmc.ncbi.nlm.nih.gov/articles/PMC7362544/)) is a sample-swap and relatedness checker.
Here, we have constructed a nextflow workflow to fit our needs for trio-based relatedness QC as well as patient-level QC from cancer-related sequencing.


<p align="center">
  <img src="https://raw.githubusercontent.com/kids-first/Kids-First-Somalier-NF-Workflow/refs/heads/master/docs/logo/kids_first_logo.svg" alt="Kids First repository logo" width="660px" />
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
#### `result interpret`
- `swap_threshold`: Relatedness threshold to consider samples as related in sample swap check. Default `0.8`

## Outputs
### `extract`
- `*.somalier`: List of extracted sites files. Necessary/recommended for repeated analyses using the somalier suite
### `relate`
- `.html`: interactive html with various QA metrics plots
- `.samples.tsv`: .ped like file with extra QC columns
- `.pairs.tsv`: shows IBS (identity by state) for all possible sample pairs
- `.groups.tsv`: shows pairs of samples above a certain relatedness
### `result interpret`
Custom script is run to summarize if errors were found in relationship and/or sex (based on ped input) or if samples swaps found (based on pairs input).
Will output a flag to STDOUT of either `PASS` if all checks passed, or `FAIL, {n} errors` with total number errors found in all checks
#### Swap example, *.swaps_summary.tsv file
```
sample_1        sample_2        concordance_score       passes_0.6
BS_FC3BZY2G     BS_F6ZHHA54     1.000   PASS
BS_9YPJANGX     BS_AF6A572P     1.000   PASS
BS_9YPJANGX     BS_HB03GSHF     0.500   FAIL
BS_B5V3KSQY     BS_RZN71A5Z     1.000   PASS
BS_B5V3KSQY     BS_ZMZTCQRM     0.998   PASS
BS_PYYNXW86     BS_3RYXSDKF     1.000   PASS
```

#### Family example *.family_summary.tsv
```
#family_id      sample_id       paternal_id     maternal_id     sex     phenotype       check_status
FM_N6BZW43Q     BS_KZT7FAEW     BS_XG2AF312     BS_F3QBHFGD     1       2       SEX: Labeled male, predicted female; RELATIONSHIP: Incorrect maternal_id
FM_N6BZW43Q     BS_XG2AF312     0       0       1       1       PASS
FM_N6BZW43Q     BS_F3QBHFGD     0       0       2       1       SEX: Labeled female, predicted male
```

## Result interpretation guidelines
If the result interpretation script outputs to STDOUT `PASS`, nothing to do, congrats! If it says `FAIL`, untar the `relate` tar ball and do the following:

- Review the `*_summary.tsv` file(s). This will tell you which samples have problems.
- If `FAIL` is seen in the swaps summary
  - Check the pairs.tsv file frm the tar ball to see if another sample ended up having a passing concordance score
  - If there is no better match, and you have more candidates, add those to the workflow, re-run, and check the pairs file again
- If `FAIL` is in the family summary
  - Update/correct the sex in the ped file based on the results is `SEX` was the error
  - If relationship is the issue, check the pairs tsv file and review the `relatedness` score.
  - Similar to swaps, you can add more samples that are candidates, and re-run and review pairs to see if another sample has an expected `relatedness` score