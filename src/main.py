import argparse
import shutil
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytrec_eval
from loguru import logger
from rich.console import Console
from rich.table import Table

SUBMISSIONS = 3
VALID_SUFFIXES = [".res", ".txt"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Script for evaluating MAP")
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Input Directory contains a list of zips",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output Directory for "
        "extracted folders, if not specified. create a temporary folder ",
    )
    parser.add_argument("-q", "--qrels", help="Qrels file")
    return parser.parse_args()


def extract_files(input_folder: Path, output_folder: Path) -> None:
    logger.info("Extracting zip files")
    files = input_folder.glob("*.zip")
    for zip_file in files:
        team_name = zip_file.stem
        if not zipfile.is_zipfile(zip_file):
            continue

        with zipfile.ZipFile(zip_file, "r") as zip_ref:
            submissions = 0
            for member in zip_ref.infolist():
                if "MACOSX" in member.filename:
                    continue

                file_extension = member.filename.split(".")[-1]
                if f".{file_extension}" in VALID_SUFFIXES:
                    submissions += 1
            if submissions != SUBMISSIONS:
                logger.error(f"{team_name} didn't submit 3 results")
                continue
            output_zip_folder = output_folder / team_name
            output_zip_folder.mkdir(exist_ok=True)

            zip_ref.extractall(output_zip_folder)


def calculate_metrics(
    qrel: defaultdict[Any, dict],
    run_file: Path,
    metrics: set[str] | None = None,
) -> tuple[float, float]:
    if metrics is None:
        metrics = {"map", "P_5"}

    with run_file.open("r") as f_run:
        run = pytrec_eval.parse_run(f_run)

    evaluator = pytrec_eval.RelevanceEvaluator(qrel, metrics)

    evaluation = evaluator.evaluate(run)

    ap = np.average([entry["map"] for entry in evaluation.values()])
    p_5 = np.average([entry["P_5"] for entry in evaluation.values()])

    return float(ap), float(p_5)


def get_table(qrel: defaultdict[Any, dict], folder: Path) -> pd.DataFrame:
    columns = ["Team", "Run", "MAP", "P@5"]
    results = pd.DataFrame(columns=columns)
    logger.info("Calculating MAP and P@5 for each run")
    for team_folder in folder.iterdir():
        if not team_folder.is_dir():
            continue

        for run in team_folder.iterdir():
            if run.suffix not in [".res", ".txt"]:
                continue

            ap, p_5 = calculate_metrics(qrel, run)
            record = {
                "Team": team_folder.name,
                "Run": run.stem,
                "MAP": ap,
                "P@5": p_5,
            }
            results = pd.concat([results, pd.DataFrame([record])], ignore_index=True)
    return results


def print_table(results: pd.DataFrame, title: str = "Winners") -> None:
    console = Console()
    table = Table(title=title)
    table.add_column("Index")
    for col in results.columns:
        table.add_column(col)

    for index, row in results.iterrows():
        table.add_row(str(index), *map(str, row))

    console.print(table)


def main() -> None:
    logger.info("Starting")
    args = parse_args()
    input_folder = Path(args.input)
    output_folder = args.output
    qrels_file = Path(args.qrels)

    if not qrels_file.exists() or not qrels_file.is_file():
        logger.error("Qrels file does not exist")
        return

    with qrels_file.open("r") as q_file:
        qrel = pytrec_eval.parse_qrel(q_file)

    if output_folder is None:
        logger.debug("Setting temp folder")
        output_folder = tempfile.mkdtemp()

    output_folder = Path(output_folder)
    if not output_folder.exists():
        logger.error("Output folder does not exist")
        return

    if not output_folder.is_dir():
        logger.error("Output folder is not a directory")
        return

    if len(list(output_folder.iterdir())) != 0:
        logger.error("Output folder is not empty")
        return

    extract_files(input_folder, output_folder)
    results = get_table(qrel, output_folder)
    logger.info(f"Average MAP for all off the class is {results["MAP"].mean()}")
    sorted_results = results.sort_values(
        by=["MAP", "P@5"],
        ascending=[False, False],
    ).drop_duplicates(["Team"])

    if args.output is None:
        shutil.rmtree(output_folder)
        print_table(sorted_results)

    else:
        output_file = output_folder / "sorted_results.csv"
        sorted_results.to_csv(output_file)
        logger.info(f"Saved results to {output_file}")

    print_table(results, title="All results, unsorted")


if __name__ == "__main__":
    main()
