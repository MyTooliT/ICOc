# -- Imports ------------------------------------------------------------------

from argparse import ArgumentParser
from glob import glob
from os import remove
from pathlib import Path

# -- Main ---------------------------------------------------------------------


def main():
    parser = ArgumentParser(
        description="Remove log and PDF files from the repository root"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print name of removed files",
    )
    verbose = parser.parse_args().verbose

    repo_path = Path(__file__).parent.parent.parent
    patterns = [
        "*.txt",
        "*.hdf5",
        "*.pdf",
        "can.log",
        "cli.log",
        "network.log",
        "plotter.log",
    ]
    files = []
    for pattern in patterns:
        files.extend(glob(f"{repo_path}/{pattern}"))

    if verbose:
        print(f"Cleaning directory {repo_path}")
    for filepath in files:
        if verbose:
            print(f"Remove {Path(filepath).name}")
        remove(filepath)


if __name__ == "__main__":
    main()
