"""
Find lines of code that were not covered by a unit test, but are hit by doing
a typical user opration with a file.
"""

import json
import os
from pathlib import Path

import coverage
import pytest
from PyPDF2 import PdfMerger, PdfReader
from rich.progress import track


def get_text(path):
    reader = PdfReader(path)
    for page in reader.pages:
        text = page.extract_text()


def get_metadata(path):
    reader = PdfReader(path)
    reader.metadata


def make_compress(path):
    reader = PdfReader(path)
    for page in reader.pages:
        page.compress_content_streams()


def make_get_fields(path):
    reader = PdfReader(path)
    with open("tmp.txt", "w") as fp:
        reader.get_fields(fileobj=fp)


def make_merge(path):
    reader = PdfReader(path)
    merger = PdfMerger()
    merger.append(reader)
    merger.write("tmp.merged.pdf")


def make_xfa(path):
    reader = PdfReader(path)
    if reader.xfa:
        print(path)
        print(reader.xfa)


def load():
    path = CACHE_FILE_NAME
    if not os.path.exists(path):
        return {}
    else:
        with open(path) as fp:
            return json.load(fp)


def store(file2cov):
    with open(CACHE_FILE_NAME, "w") as fp:
        fp.write(json.dumps(file2cov, indent=4))


def main():
    root = Path("pdf")
    paths = sorted(list(root.glob("*.pdf")))

    source_files = [
        "/home/moose/Github/py-pdf/PyPDF2/PyPDF2/_reader.py",
        "/home/moose/Github/py-pdf/PyPDF2/PyPDF2/_writer.py",
        "/home/moose/Github/py-pdf/PyPDF2/PyPDF2/_merger.py",
        "/home/moose/Github/py-pdf/PyPDF2/PyPDF2/_cmap.py",
        "/home/moose/Github/py-pdf/PyPDF2/PyPDF2/_page.py",
        "/home/moose/Github/py-pdf/PyPDF2/PyPDF2/_utils.py",
        "/home/moose/Github/py-pdf/PyPDF2/PyPDF2/generic.py",
        "/home/moose/Github/py-pdf/PyPDF2/PyPDF2/filters.py",
    ]

    tst_cov = coverage.Coverage()
    tst_cov.start()
    pytest.main(["/home/moose/Github/py-pdf/PyPDF2"])
    tst_cov.stop()
    tst_cov.save()
    data = tst_cov.get_data()
    file2cov_base = {}
    for src_file in source_files:
        file2cov_base[src_file] = data.lines(src_file)
        assert file2cov_base[src_file] is not None

    file2cov = load()
    i = 0
    for path in track(paths):
        str_path = str(path)
        if str_path in file2cov:
            continue
        cov = coverage.Coverage()
        cov.start()
        try:
            OPERATION(path)
        except Exception:
            pass
        cov.stop()
        cov.save()
        data = cov.get_data()

        file2cov[str_path] = {}
        i += 1
        for src_file in source_files:
            added = data.lines(src_file)
            if added is None:
                continue
            new_lines = sorted(list(set(added) - set(file2cov_base[src_file])))
            if new_lines:
                file2cov[str_path][src_file] = new_lines
                store(file2cov)
        if i % 10 == 0:
            store(file2cov)
    store(file2cov)


OPERATION = make_merge
CACHE_FILE_NAME = "cache-merge.json"

if __name__ == "__main__":
    main()
