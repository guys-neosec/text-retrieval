import argparse
import sys
import tempfile
import time
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import TextIO

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


def main() -> None:
    logger.info("Starting")
    args = parse_args()
    input_folder = Path(args.input)
    output_folder = args.output
    qrels_file = Path(args.qrels)
    if not qrels_file.exists() or not qrels_file.is_file():
        logger.error("Qrels file does not exist")
        return
    if output_folder is None:
        logger.debug("Setting temp folder")
        output_folder = tempfile.mkstemp()
    output_folder = Path(output_folder)
    extract_files(input_folder, output_folder)


if __name__ == "__main__":
    main()
