#!/usr/bin/env python3

"""Interpret somalier results and report errors on relationship and sex, or sample swaps depending on inputs given.

For relationships and sex, like trios, need input ped file and output .samples.tsv.
For samples swaps, need input groups csv file and output .groups.tsv.
"""

import argparse
import csv
import sys


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Interpret somalier results for relationships and sex or samples swaps."
    )
    parser.add_argument("--ped", help="Input PED file for relationships")
    parser.add_argument("--samples-tsv", help="Output samples TSV file from somalier")
    parser.add_argument("--groups-csv", help="Input groups CSV file for sample swaps")
    parser.add_argument("--groups-tsv", help="Output groups TSV file from somalier")
    parser.add_argument(
        "--output-prefix", help="Prefix for output error files", default="somalier_interpret"
    )
    parser.add_argument("--swap-threshold", help="Relatedness threshold for sample swaps",
                        type=float, default=0.8)
    return parser.parse_args()


def check_relationships(
    ped_entry: str,
    check_result: str,
    err_dict: dict[str, list[str]],
    p_errs: int,
) -> tuple[dict[str, list[str]], int]:
    """Comare expected relationship from PED to somalier check result."""
    if ped_entry != check_result:
        if ped_entry not in err_dict:
            err_dict[ped_entry] = []
        err_dict[ped_entry].append("relation")
        p_errs += 1
    return err_dict, p_errs


def check_ped(ped_file: str, samples_tsv: str, out: str) -> None:
    """Read in ped and samples as dicts and check family relationships and sex.

    Args:
        ped_file (str): Path to PED file
        samples_tsv (str): Path to samples TSV file

    """
    # keep track of relatedness and sex errors per sample
    rel_err_dict: dict[str, list[str]] = {}

    with open(ped_file) as ped_f, open(samples_tsv) as samples_f:
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
                msg = f"Sample {sample_id} in PED file not found in samples TSV."
                raise KeyError(msg)
            sample_row = samples_data[sample_id]
            # check sex
            if ped_sex_dict[sample_row["sex"]] != sample_row["original_pedigree_sex"]:
                if sample_id not in rel_err_dict:
                    rel_err_dict[sample_id] = []
                rel_err_dict[sample_id].append("sex")
            if ped_row["paternal_id"] != "0" or ped_row["maternal_id"] != "0":
                parent_errors = 0

                rel_err_dict, parent_errors = check_relationships(
                    ped_row["paternal_id"], sample_row["paternal_id"], rel_err_dict, parent_errors
                )
                rel_err_dict, parent_errors = check_relationships(
                    ped_row["maternal_id"], sample_row["maternal_id"], rel_err_dict, parent_errors
                )
            # if both parents have errors, add proband error
            if parent_errors == 2:
                if sample_id not in rel_err_dict:
                    rel_err_dict[sample_id] = []
                rel_err_dict[sample_id].append("relation")
    # Print out error file if any errors found
    if rel_err_dict:
        outfile = f"{out}.somalier_relation_errors.tsv"
        with open(outfile, "w") as out_f:
            print("sample_id\terror_types", file=out_f)
            for sample, errors in rel_err_dict.items():
                print(f"{sample}\t{','.join(errors)}", file=out_f)
        print(f"Relationship and/or sex erros found. See {outfile} for details.", file=sys.stderr)
    else:
        print("No relationship and/or sex errors found.", file=sys.stderr)


def check_sample_swaps(groups_csv: str, groups_tsv: str, out: str, swap_t: float = 0.8) -> None:
    """Check for sample swaps using groups CSV and groups TSV files.

    group csv simply has all sample from same patient together as a csv per line.
    group tsv has pairwise relatedness info.
    therefore we need to group all above a certain relatedness threshold to get the complete set and check against csv.
    Easiest way to check would be to create one pairwise comparison set based on input, and just compare results

    Args:
        groups_csv (str): Path to groups CSV file
        groups_tsv (str): Path to groups TSV file
        out (str): Output prefix for error file
        swap_t (float): Relatedness threshold to consider samples as related

    """
    with open(groups_csv) as csv_f, open(groups_tsv) as tsv_f:
        # Read input groups CSV
        csv_groups: dict[str, set[str]] = {}
        for line in csv_f:
            samples = line.strip().split(",")
            # Use first sample as group ID
            csv_groups[samples[0]] = set(samples[1:])
        # Read output groups TSV
        tsv_groups: dict[str, set[str]] = {}
        for line in tsv_f:
            sample_csv, relatedness = line.strip().split("\t")
            sample_a, sample_b = sample_csv.split(",")
            if float(relatedness) >= swap_t:
                if sample_a in csv_groups:
                    index_sample = sample_a
                    comparator_sample = sample_b
                elif sample_b in csv_groups:
                    index_sample = sample_b
                    comparator_sample = sample_a
                else:
                    continue
            else:
                continue
            if index_sample not in tsv_groups:
                tsv_groups[index_sample] = set()
            tsv_groups[index_sample].add(comparator_sample)
        diff_list: list[str] = []
        for sample, sample_set in csv_groups.items():
            group_diff = sample_set - tsv_groups.get(sample, set())
            if group_diff:
                diff_list.append(f"{sample}\t{','.join(group_diff)}")
        # Print out error file if any differences found
        if diff_list:
            outfile = f"{out}.somalier_sample_swap_errors.tsv"
            with open(outfile, "w") as out_f:
                print("sample_id\tswapped_samples", file=out_f)
                print("\n".join(diff_list), file=out_f)
            print(f"Sample swaps found. See {outfile} for details.", file=sys.stderr)


def main() -> None:
    """Parse args and run appropriate checks."""
    args = parse_args()
    if (args.ped and args.samples_tsv) or (args.groups_csv and args.groups_tsv):
        if args.ped and args.samples_tsv:
            print(
                f"Checking relationship and sex errors using {args.ped} and {args.samples_tsv}",
                file=sys.stderr,
            )
            check_ped(args.ped, args.samples_tsv, args.output_prefix)
        if args.groups_csv and args.groups_tsv:
            print(
                f"Checking sample swaps using {args.groups_csv} and {args.groups_tsv}",
                file=sys.stderr,
            )
            check_sample_swaps(args.groups_csv, args.groups_tsv, args.output_prefix,
                               args.swap_threshold)
    else:
        print(
            "Insufficient arguments provided. Please provide either PED and samples TSV "
            "for relationship checks or groups CSV and groups TSV for sample swap checks.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
