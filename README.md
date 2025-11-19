# Kids First DRC Somalier QC
Somalier ([git repo](https://github.com/brentp/somalier/tree/v0.3.1), [publication](https://pmc.ncbi.nlm.nih.gov/articles/PMC7362544/)) is a sample-swap and relatedness checker.
Here, we have constructed a nextflow workflow to fit our needs for trio-based relatedness QC as well as patient-level QC from cancer-related sequencing.


<p align="center">
  <img src="docs/logo/kids_first_logo.svg" alt="Kids First repository logo" width="660px" />
</p>
<p align="center">
  <a href="https://github.com/kids-first/Kids-First-Somalier-NF-Workflow/blob/main/LICENSE"><img src="https://img.shields.io/github/license/kids-first/Kids-First-Somalier-NF-Workflow.svg?style=for-the-badge"></a>
</p>

## Inputs
The workflow is designed to run `extract` to create the somalier extracted sites file if needed (from alignment), then run `relate` to get various relatedness, sex, and sample-swap QC metrics.
The `.somalier` formatted files can br provided directly as well, and are worth keeping as they are fairly small and can be used for future comparisons and ancestry predictions (not in this workflow)