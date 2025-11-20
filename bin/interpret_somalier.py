#!/usr/bin/env python3

"""Interpret somalier results and report errors on relationship and sex, or sample swaps depending on inputs given.

For relationships and sex, like trios, need input ped file and output .samples.tsv.
For samples swaps, need input groups csv file and output .groups.tsv.
"""

import argparse
import csv

import pandas as pd


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Interpret somalier results for relationships and sex or samples swaps."
    )
    parser.add_argument("--ped", help="Input PED file for relationships")
    parser.add_argument("--samples_tsv", help="Output samples TSV file from somalier")
    parser.add_argument("--groups_csv", help="Input groups CSV file for sample swaps")
    parser.add_argument("--groups_tsv", help="Output groups TSV file from somalier")
    return parser.parse_args()


def check_ped(ped_file: str, samples_tsv: str) -> None:
    """Read in ped and samples as dicts and check family relationships and sex.

    Args:
        ped_file (str): Path to PED file
        samples_tsv (str): Path to samples TSV file

    """
    with open(ped_file, "r") as ped_f, open(samples_tsv, "r") as samples_f:
        ped_fields: list[str] = [
            "#family_id",
            "sample_id",
            "paternal_id",
            "maternal_id",
            "sex",
            "phenotype",
        ]
        ped_reader: csv.DictReader = csv.DictReader(ped_f, delimiter="\t", fieldnames=ped_fields)
        samples_reader: csv.DictReader = csv.DictReader(samples_f, delimiter="\t")
        ped_data: dict[str, dict[str, str]] = {row["sample_id"]: row for row in ped_reader}
        samples_data: dict[str, dict[str, str]] = {row["sample_id"]: row for row in samples_reader}
        ped_sex_dict: dict[str, str] = {"1": "male", "2": "female", "0": "unknown"}
        # iterate through sample IDs in ped, check sex for each, relationship for proband
        for sample_id, ped_row in ped_data.items():
            if sample_id not in samples_data:
                raise KeyError(f"Sample {sample_id} in PED file not found in samples TSV.")
            sample_row = samples_data[sample_id]
            # check sex
            if ped_sex_dict[sample_row["sex"]] != sample_row["original_sex_pedigree"]:
                print(f"Sex error for sample {sample_id}")
            if ped_row["paternal_id"] != "0" or ped_row["maternal_id"] != "0":
                # check relationships for proband
                print(f"Checking relationships for proband {sample_id}")
                if sample_row["paternal_id"] != ped_row["paternal_id"]:
                    print(f"Parent with ID {ped_row['paternal_id']} does not seem be related with {sample_id}")
                if sample_row["maternal_id"] != ped_row["maternal_id"]:
                    print(f"Parent with ID {ped_row['maternal_id']} does not seem be related with {sample_id}")



def check_sample_swaps(groups_csv: str, groups_tsv: str) -> None:
    """Check for sample swaps using groups CSV and groups TSV files.

    group csv simply has all sample from same patient together as a csv per line.
    group tsv has pairwise relatedness info.
    therefore we need to group all above a certain relatedness threshold to get the complete set and check against csv.
    Esiest way to check would be to create one pairwise comparison set based on input, and just compare results

    Args:
        groups_csv (str): Path to groups CSV file
        groups_tsv (str): Path to groups TSV file

    """



def main() -> None:
    """Main function to parse args and run appropriate checks."""
    args = parse_args()
    if args.ped and args.samples_tsv:
        check_ped(args.ped, args.samples_tsv)
    elif args.groups_csv and args.groups_tsv:
        # Placeholder for sample swap checking logic
        print(f"Checking sample swaps using {args.groups_csv} and {args.groups_tsv}")
        check_sample_swaps(args.groups_csv, args.groups_tsv)
    else:
        print(
            "Insufficient arguments provided. Please provide either PED and samples TSV for relationship checks or groups CSV and groups TSV for sample swap checks."
        )


if __name__ == "__main__":
    main()
