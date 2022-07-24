"""
Find lines of code that were not covered by a unit test, but are hit by doing
a typical user opration with a file.
"""

import json
import os
import time
import warnings
from pathlib import Path
import time
from typing import List, Dict

import coverage
import pytest
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PyPDF2.filters import _xobj_to_image
from rich.progress import track
from PyPDF2.constants import (
    Ressources as RES,
    PageAttributes as PG,
    ImageAttributes as IA,
)
import warnings

warnings.filterwarnings("ignore")


warnings.filterwarnings("ignore")


def run_get_text(path):
    reader = PdfReader(path)
    for page in reader.pages:
        text = page.extract_text()


def run_get_metadata(path):
    reader = PdfReader(path)
    reader.metadata


def run_compress(path):
    reader = PdfReader(path)
    for page in reader.pages:
        page.compress_content_streams()


def run_get_fields(path):
    reader = PdfReader(path)
    with open("tmp.txt", "w") as fp:
        reader.get_fields(fileobj=fp)


def run_merge(path):
    reader = PdfReader(path)
    merger = PdfMerger()
    merger.append(reader)
    merger.write("tmp.merged.pdf")


def run_overlay(path):
    reader = PdfReader(path)
    writer = PdfWriter()

    reader_overlay = PdfReader("overlay.pdf")
    overlay = reader_overlay.pages[0]

    for page in reader.pages:
        page.merge_page(overlay)
        writer.add_page(page)
    with open("tmp.merged.pdf", "wb") as fp:
        writer.write(fp)


def run_xfa(path):
    reader = PdfReader(path)
    reader.xfa


def run_scale_page(path):
    reader = PdfReader(path)
    for page in reader.pages:
        page.scale(sx=2, sy=3)


def run_get_outlines(path):
    reader = PdfReader(path)
    reader.outlines


def run_get_fonts(path):
    reader = PdfReader(path)
    for page in reader.pages:
        page._get_fonts()


def run_extract_images(path):
    reader = PdfReader(path)

    images_extracted = []
    root = Path("extracted-images")
    if not root.exists():
        os.mkdir(root)

    for page in reader.pages:
        if RES.XOBJECT in page[PG.RESOURCES]:
            x_object = page[PG.RESOURCES][RES.XOBJECT].get_object()

            for obj in x_object:
                if x_object[obj][IA.SUBTYPE] == "/Image":
                    extension, byte_stream = _xobj_to_image(x_object[obj])
                    if extension is not None:
                        filename = root / (obj[1:] + ".png")
                        with open(filename, "wb") as img:
                            img.write(byte_stream)
                        images_extracted.append(filename)

    # Cleanup
    for filepath in images_extracted:
        if os.path.exists(filepath):
            os.remove(filepath)


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


def filter_full_coverage(
    source_files: List[str], file2cov_base: Dict[str, List[int]]
) -> List[str]:
    new_source_files = []
    for file in source_files:
        with open(file) as fp:
            nb_lines = len(fp.readlines())
        covered = len(set(file2cov_base[file]))
        if nb_lines <= covered:
            print(f"{file} has {nb_lines} lines, covered {covered}. Skip it")
        else:
            new_source_files.append(file)
    return new_source_files


def main(OPERATION, CACHE_FILE_NAME):
    root = Path("pdf")
    paths = sorted(list(root.glob("*.pdf")))

    source_files = [
        "/home/moose/Github/py-pdf/PyPDF2/PyPDF2/_cmap.py",
        "/home/moose/Github/py-pdf/PyPDF2/PyPDF2/_encryption.py",
        "/home/moose/Github/py-pdf/PyPDF2/PyPDF2/_merger.py",
        "/home/moose/Github/py-pdf/PyPDF2/PyPDF2/_page.py",
        "/home/moose/Github/py-pdf/PyPDF2/PyPDF2/_reader.py",
        "/home/moose/Github/py-pdf/PyPDF2/PyPDF2/_utils.py",
        "/home/moose/Github/py-pdf/PyPDF2/PyPDF2/_writer.py",
        "/home/moose/Github/py-pdf/PyPDF2/PyPDF2/filters.py",
        "/home/moose/Github/py-pdf/PyPDF2/PyPDF2/generic.py",
        "/home/moose/Github/py-pdf/PyPDF2/PyPDF2/pagerange.py",
        "/home/moose/Github/py-pdf/PyPDF2/PyPDF2/xmp.py",
    ]

    tst_cov = coverage.Coverage(branch=True)
    tst_cov.start()
    pytest.main(["/home/moose/Github/py-pdf/PyPDF2"])
    tst_cov.stop()
    tst_cov.save()
    data = tst_cov.get_data()
    file2cov_base = {}
    for src_file in sorted(data.measured_files()):
        if "/tests/" in src_file:
            continue
        print(src_file)
        file2cov_base[src_file] = data.arcs(src_file)
        assert file2cov_base[src_file] is not None, f"{src_file} has no coverage"

    source_files = filter_full_coverage(source_files, file2cov_base)

    file2cov = load()
    timings = []  # TODO: load and store!
    i = 0
    for path in track(paths):
        str_path = str(path)
        if str_path in file2cov:
            continue
        cov = coverage.Coverage(branch=True)
        cov.start()
        try:
            t0 = time.time()
            OPERATION(path)
            t1 = time.time()
            timings.append(t1 - t0)
        except Exception as exc:
            print((path, exc))
            # raise # todo: actually fail
            continue
        cov.stop()
        cov.save()
        data = cov.get_data()

        file2cov[str_path] = {}
        i += 1
        for src_file in data.measured_files():
            if src_file.endswith("get_coverage_by_pdf.py"):
                continue
            added = data.arcs(src_file)
            if added is None:
                print(f"None! For {path}")
                continue
            if src_file not in file2cov_base:
                print(f"Not found via tests!: {src_file}")
                file2cov_base[src_file] = []
            new_lines = sorted(list(set(added) - set(file2cov_base[src_file])))
            if new_lines:
                file2cov[str_path][src_file] = new_lines
                store(file2cov)
        if i % 10 == 0:
            store(file2cov)
    store(file2cov)


if __name__ == "__main__":
    m = (
        # ("cache-extract-images.json", run_extract_images),
        # ("cache-get-fonts.json", run_get_fonts),
        # ("cache-get-metadata.json", run_get_metadata),
        # ("cache-get-fields.json", run_get_fields),
        ("cache-get-outlines.json", run_get_outlines),
        ("cache-get_xfa.json", run_xfa),
        ("cache-overlay.json", run_overlay),
        ("cache-make-scale.json", run_scale_page),
        ("cache-get-text.json", run_get_text),
        ("cache-make_merge.json", run_merge),
        ("cache-make_compress.json", run_compress),
    )

    for CACHE_FILE_NAME, OPERATION in m:
        print(f"## {CACHE_FILE_NAME} starts...")
        main(OPERATION, CACHE_FILE_NAME)
