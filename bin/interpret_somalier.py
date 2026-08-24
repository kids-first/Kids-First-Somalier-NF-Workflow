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
    parser.add_argument("--pairs-tsv", help="Output groups TSV file from somalier")
    parser.add_argument(
        "--output-prefix", help="Prefix for output error files", default="somalier_interpret"
    )
    parser.add_argument("--swap-threshold", help="Relatedness threshold for sample swaps",
                        type=float, default=0.8)
    args = parser.parse_args()
    if not any([(args.ped and args.samples_tsv), (args.groups_csv, args.pairs_tsv)]):
        parser.error("Must provide either --ped and --samples-tsv or --groups-csv and --pairs-tsv!")
    return args


def check_ped(
    ped_file: str, samples_tsv: str, errs_dict: dict[str, dict[str, str]]
) -> dict[str, dict[str, str]]:
    """Read in ped and samples as dicts and check family relationships and sex.

    Args:
        ped_file (str): Path to PED file
        samples_tsv (str): Path to samples TSV file
        errs_dict (dict): Dictionary to store relation and sex errors

    Returns:
        dict: Updated errs_dict with any found errors

    """
    # keep track of relatedness and sex errors per sample

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
        errs_dict[sample_id] = {}
        if sample_id not in samples_data:
            msg = f"Sample {sample_id} in PED file not found in samples TSV."
            raise KeyError(msg)
        sample_row = samples_data[sample_id]
        # check sex
        predicted_sex = ped_sex_dict[sample_row["sex"]]
        user_ped_sex = sample_row["original_pedigree_sex"]
        if predicted_sex != user_ped_sex:
            errs_dict[sample_id]["SEX"] = f"Labeled {user_ped_sex}, predicted {predicted_sex}"
        parent_errors = 0
        for column in ["paternal_id", "maternal_id"]:
            ped_parent = ped_row[column]
            predicted_parent = sample_row[column]
            if ped_parent not in ("0", predicted_parent):
                parent_errors += 1
                errs_dict[sample_id] = {"RELATIONSHIP": f"Incorrect {column}"}
        # if both parents have errors, collapse to say both parents wrong
        if parent_errors == 2:
            errs_dict[sample_id] = {"RELATIONSHIP": "Incorrect paternal and maternal IDs"}
    return errs_dict


def check_sample_swaps(
    groups_csv: str, pairs_tsv: str, errs_dict: dict[str, dict[str, str]], swap_t: float = 0.8,
) -> dict[str, dict[str, str]]:
    """Check for sample swaps using groups CSV and pairs TSV files.

    group csv simply has all sample from same patient together as a csv per line.
    pairs tsv has pairwise concordance info.
    Therefore we need to group all above a certain concordance threshold to get the complete set and check against csv.
    Easiest way to check would be to create one pairwise comparison set based on input, and just compare results
    to see if all samples at or above threshold in the tsv group are in the input csv group.

    Args:
        groups_csv (str): Path to groups CSV file
        pairs_tsv (str): Path to pairs TSV file
        errs_dict (dict): Dictionary to store swap errors
        swap_t (float): Concordance threshold to consider samples as related

    Returns:
        dict: Updated errs_dict with any found errors

    """
    with open(groups_csv) as csv_f:
        # Read input groups CSV
        csv_groups: dict[str, set[str]] = {}
        for line in csv_f:
            samples = line.strip().split(",")
            # Use first sample as group ID
            csv_groups[samples[0]] = set(samples[1:])
    # Read output pairs TSV
    with open(pairs_tsv) as tsv_f:
        tsv_groups: dict[str, set[str]] = {}
        head = next(tsv_f)
        header = head.strip().split("\t")
        concordance_index = header.index("concordance")
        for line in tsv_f:
            data = line.strip().split("\t")
            sample_a, sample_b, concordance = (data[0], data[1], data[concordance_index])
            if float(concordance) < swap_t:
                continue
            if sample_a in csv_groups:
                index_sample = sample_a
                comparator_sample = sample_b
            elif sample_b in csv_groups:
                index_sample = sample_b
                comparator_sample = sample_a
            else:
                continue
            if index_sample not in tsv_groups:
                tsv_groups[index_sample] = set()
            tsv_groups[index_sample].add(comparator_sample)
        for sample, sample_set in csv_groups.items():
            group_diff = sample_set - tsv_groups.get(sample, set())
            if sample not in errs_dict:
                    errs_dict[sample] = {}
            if group_diff:
                errs_dict[sample]["SWAP"] = (
                    f"Failed concordance threshold {swap_t}: {','.join(group_diff)}"
                )
        return errs_dict


def main() -> None:
    """Parse args and run appropriate checks."""
    args = parse_args()
    err_filter = """\
##FILTER=<ID=RELATION,Description="Sample has relationship errors">
##FILTER=<ID=SEX,Description="Incorrect SEX assignment">
##FILTER=<ID=SWAP,Description="Sample swap detected">
##FILTER=<ID=PASS,Description="No errors detected">
#SAMPLE\tFILTER\tINFO"""
    errs_dict: dict[str, dict[str, str]] = {}
    if args.ped and args.samples_tsv:
        print(
            f"Checking relationship and sex errors using {args.ped} and {args.samples_tsv}",
            file=sys.stderr,
        )
        errs_dict.update(check_ped(args.ped, args.samples_tsv, errs_dict))
    if args.groups_csv and args.pairs_tsv:
        print(
            f"Checking sample swaps using {args.groups_csv} and {args.pairs_tsv}",
            file=sys.stderr,
        )
        errs_dict.update(check_sample_swaps(
            args.groups_csv, args.pairs_tsv, errs_dict, args.swap_threshold
        ))
    err_flag = "PASS"
    with open(args.output_prefix + ".somalier_interpretation.tsv", "w") as out_f:
        print(err_filter, file=out_f)
        for sample_id, error_info in errs_dict.items():
            if not error_info:
                print(f"{sample_id}\tPASS\t", file=out_f)
            else:
                err_flag = "FAIL"
                filter_list = ";".join(error_info.keys())
                info_list = ";".join([f"{key}={value}" for key, value in error_info.items()])
                print(f"{sample_id}\t{filter_list}\t{info_list}", file=out_f)
    # For workflow purposes, print overall status
    print(err_flag)


if __name__ == "__main__":
    main()
