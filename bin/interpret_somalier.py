#!/usr/bin/env python3

"""Interpret somalier results and report errors on relationship and sex, or sample swaps depending on inputs given.

For relationships and sex, like trios, need input ped file and output .samples.tsv.
For samples swaps, need input groups csv file and output .groups.tsv.
"""

import argparse
import csv
import sys
from typing import IO


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
    ped_file: str, samples_tsv: str, fam_out: IO
) -> int:
    """Read in ped and samples as dicts and check family relationships and sex.

    Args:
        ped_file (str): Path to PED file
        samples_tsv (str): Path to samples TSV file
        fam_out (IO): File handle to write family summary output

    Returns:
        int: 0 if no errors, otherwise > 0.

    """
    # keep track of relatedness and sex errors per sample
    status: int = 0
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
    errs_dict: dict[str, dict[str, str]] = {}
    print("\t".join(ped_fields) + "\tcheck_status", file=fam_out)
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
            status += 1
        parent_errors = 0
        for column in ["paternal_id", "maternal_id"]:
            ped_parent = ped_row[column]
            predicted_parent = sample_row[column]
            if ped_parent not in ("0", predicted_parent):
                parent_errors += 1
                errs_dict[sample_id]["RELATIONSHIP"] = f"Incorrect {column}"
                status += 1
        # if both parents have errors, collapse to say both parents wrong
        if parent_errors == 2:
            errs_dict[sample_id]["RELATIONSHIP"] = "Incorrect paternal and maternal IDs"

        print("\t".join(ped_row.values()), file=fam_out, end="\t")
        if errs_dict.get(sample_id):
            print("; ".join([f"{k}: {v}" for k, v in errs_dict[sample_id].items()]), file=fam_out)
        else:
            print("PASS", file=fam_out)
    return status


def check_sample_swaps(
    groups_csv: str,
    pairs_tsv: str,
    swap_f: IO,
    swap_t: float = 0.8
) -> int:
    """Check for sample swaps using groups CSV and pairs TSV files.

    group csv simply has all sample from same patient together as a csv per line.
    pairs tsv has pairwise concordance info.
    We save each sample grouping as a set, and search for each pair in the list of sets, and check if concordance is above threshold.

    Args:
        groups_csv (str): Path to groups CSV file
        pairs_tsv (str): Path to pairs TSV file
        swap_t (float): Concordance threshold to consider samples as related
        swap_f (IO): File handle to write swap summary output

    Returns:
        int: 0 if no swaps found, otherwise the number of swap violations.

    """
    status: int = 0
    with open(groups_csv) as csv_f:
        # Save sample groupings as list of sets to search
        csv_groups: list[set[str]] = []
        for line in csv_f:
            samples = line.strip().split(",")
            csv_groups.append(set(samples))
    # Read output pairs TSV
    with open(pairs_tsv) as tsv_f:
        head = next(tsv_f)
        header = head.strip().split("\t")
        concordance_index = header.index("concordance")
        for line in tsv_f:
            data = line.strip().split("\t")
            sample_a, sample_b, concordance = (data[0], data[1], data[concordance_index])
            for sample_set in csv_groups:
                # just checking if both samples are in the same group, if so check concordance
                if sample_a in sample_set and sample_b in sample_set:
                    verdict: str = "PASS"
                    if float(concordance) < swap_t:
                        verdict = "FAIL"
                        status += 1
                    print(f"{sample_a}\t{sample_b}\t{concordance}\t{verdict}", file=swap_f)
                    break
    return status


def main() -> None:
    """Parse args and run appropriate checks."""
    args = parse_args()
    err_flag = 0
    if args.ped and args.samples_tsv:
        print(
            f"Checking relationship and sex errors using {args.ped} and {args.samples_tsv}",
            file=sys.stderr,
        )
        family_summary = args.output_prefix + ".family_summary.tsv"
        with open(family_summary, "w") as fam_out:
            err_flag += check_ped(args.ped, args.samples_tsv, fam_out)
    if args.groups_csv and args.pairs_tsv:
        print(
            f"Checking sample swaps using {args.groups_csv} and {args.pairs_tsv}",
            file=sys.stderr,
        )
        swaps_summary = args.output_prefix + ".swaps_summary.tsv"
        with open(swaps_summary, "w") as swap_f:
            print(f"sample_1\tsample_2\tconcordance_score\tpasses_{args.swap_threshold}",
                  file=swap_f)
            err_flag += check_sample_swaps(
                args.groups_csv, args.pairs_tsv, swap_f, args.swap_threshold
            )

    err_flag = "PASS" if err_flag == 0 else f"FAIL, {err_flag} errors"
    # For workflow purposes, print overall status
    print(err_flag)


if __name__ == "__main__":
    main()
