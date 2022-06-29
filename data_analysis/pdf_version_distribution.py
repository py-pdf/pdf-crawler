"""
Which versions do the downloaded PDF documents have?

Something like this:

   22,848 documents in total:
    7,842x %PDF-1.4
    4,937x %PDF-1.3
    4,524x %PDF-1.2
    1,664x %PDF-1.6
    2,522x %PDF-1.5
      868x %PDF-1.1
      401x %PDF-1.7
       83x %PDF-1.0
        1x \rTM-107
        1x \nt55-56
        1x ISSRes
        1x \r\n%PDF-1
        1x 052165
        1xfeb5.p
        1x

"""

from collections import Counter
from pathlib import Path


def get_byte(path):
    with open(path, "rb") as f:
        return f.read(8).decode("utf8")


def main():
    root = Path("../pdf")
    paths = sorted(list(root.glob("*.pdf")))

    bytes = Counter([get_byte(path) for path in paths])

    print(f"{len(paths):>9,} documents in total:")
    for pdf_header, count in bytes.items():
        pdf_header = pdf_header.replace("\n", "\\n").replace("\r", "\\r")
        print(f"{count:>9,}x {pdf_header}")


if __name__ == "__main__":
    main()
