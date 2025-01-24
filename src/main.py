import argparse
import os
import sys
import tempfile
import time
import zipfile
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any, TextIO

import pandas as pd
import pytrec_eval
from loguru import logger

SUBMISSIONS = 3


def progressbar(
    count: int,
    prefix: str = "",
    size: int = 60,
    out: TextIO = sys.stdout,
) -> Callable:
    start = time.time()  # time estimate start
    progress = 0.1

    def advance() -> float:
        nonlocal progress
        x = int(size * progress / count)
        # time estimate calculation and string
        remaining = ((time.time() - start) / progress) * (count - progress)
        mins, sec = divmod(remaining, 60)  # limited to minutes
        time_str = f"{int(mins):02}:{sec:03.1f}"
        print(
            f"{prefix}[{'█' * x}{('.' * (size - x))}] "
            f"{int(progress)}/{count} Est wait {time_str}",
            end="\r",
            file=out,
            flush=True,
        )
        progress += 1
        return progress

    return advance


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
    files = input_folder.glob("*.zip")
    progress_bar = progressbar(len(list(files)))
    for zip_file in files:
        full_path = input_folder / zip_file
        team_name = full_path.stem
        if not zipfile.is_zipfile(full_path):
            continue
        with zipfile.ZipFile(full_path, "r") as zip_ref:
            if len(zip_ref.infolist()) != SUBMISSIONS:
                logger.error(f"{team_name} didn't submit 3 results")
                continue
            output_zip_folder = output_folder / team_name
            output_zip_folder.mkdir(exist_ok=True)

            zip_ref.extractall(output_folder)
        progress_bar()


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

    return evaluation["map"], evaluation["p_5"]


def main() -> None:
    columns = ["Team", "Run", "MAP", "P@5"]
    results = pd.DataFrame(columns=columns)
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
        output_folder = tempfile.mkstemp()

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

    for entry in os.listdir(output_folder):
        team_folder = output_folder / entry
        if not team_folder.is_dir():
            logger.warning("Something went wrong here")
        for run in os.listdir(team_folder):
            run_name = run.split(".")[0]
            ap, p_5 = calculate_metrics(qrel, team_folder / run)
            record = {
                "Team": entry,
                "Run": run_name,
                "MAP": ap,
                "P@5": p_5,
            }
            results = results.append(record, ignore_index=True)


if __name__ == "__main__":
    main()
