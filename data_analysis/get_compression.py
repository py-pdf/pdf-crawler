"""Check which files can be compressed most by PyPDF2."""

import os
import warnings
from pathlib import Path

from PyPDF2 import PdfReader, PdfWriter
from rich.progress import track

warnings.filterwarnings("ignore")

import logging

logger = logging.getLogger("PyPDF2")
logger.setLevel(logging.ERROR)

import json

with open("spider-snapshot.json") as fp:
    mapping = json.load(fp)["stored_at"]


def verify_read_write(path: str) -> bool:
    reader = PdfReader(path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    writer.add_metadata(reader.metadata)

    base = os.path.basename(path)
    path_new = f"tmp/{base}"

    with open(path_new, "wb") as fp:
        writer.write(fp)

    size_old = os.path.getsize(path)
    size_new = os.path.getsize(path_new)

    if abs(size_old - size_new) > 4_000_000:
        # print(f"{size_old:>12,} vs {size_new:>12,}: {abs(size_old-size_new):12,} for {path}: {mapping[str(path)]}")
        return False
    os.remove(path_new)
    return True


def main():
    root = Path("../pdf")
    paths = sorted(list(root.glob("*.pdf")))

    for path in track(paths):
        try:
            if not verify_read_write(path):
                pass
                # print(f"Failed for {path}")
        except Exception as e:
            print(f"{mapping[str(path)]}: {e}")


if __name__ == "__main__":
    main()
