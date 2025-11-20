#!/usr/bin/env python3

"""
Interpret somalier results and report errors on relationship and sex, or sample swaps depending on inputs given

For relationships and sex, like trios, need input ped file and output .samples.tsv.
For samples swaps, need input groups csv file and output .groups.tsv.
"""
import argparse
import csv

def parse_args():
    parser = argparse.ArgumentParser(description="Interpret somalier results for relationships and sex or samples swaps.")
    parser.add_argument("--ped", help="Input PED file for relationships")
    parser.add_argument("--samples_tsv", help="Output samples TSV file from somalier")
    parser.add_argument("--groups_csv", help="Input groups CSV file for sample swaps")
    parser.add_argument("--groups_tsv", help="Output groups TSV file from somalier")
    return parser.parse_args()


def fam_check(ped_file: str, samples_tsv: str) -> None:
    """Read in ped and samples as dicts and check family relationships and sex
    
    Args:
        ped_file (str): Path to PED file
        samples_tsv (str): Path to samples TSV file
    """
    with open(ped_file, 'r') as ped_f, open(samples_tsv, 'r') as samples_f:
        ped_fields = ['#family_id', 'sample_id', 'paternal_id', 'maternal_id', 'sex', 'phenotype']
        ped_reader = csv.DictReader(ped_f, delimiter='\t', fieldnames=ped_fields)
        samples_reader = csv.DictReader(samples_f, delimiter='\t')
        ped_data = {row['sample_id']: row for row in ped_reader}
        samples_data = {row['sample_id']: row for row in samples_reader}
        # iterate through sample IDs in ped, check sex for each, relationship for proband
        for sample_id, ped_row in ped_data.items():
            if sample_id not in samples_data:
                raise KeyError(f"Sample {sample_id} in PED file not found in samples TSV.")


    print(f"Checking family relationships using {ped_file} and {samples_tsv}")

def main():
    args = parse_args()
    if args.ped and args.samples_tsv:
        fam_check(args.ped, args.samples_tsv)
    elif args.groups_csv and args.groups_tsv:
        # Placeholder for sample swap checking logic
        print(f"Checking sample swaps using {args.groups_csv} and {args.groups_tsv}")
    else:
        print("Insufficient arguments provided. Please provide either PED and samples TSV for relationship checks or groups CSV and groups TSV for sample swap checks.")


if __name__ == "__main__":
    main()