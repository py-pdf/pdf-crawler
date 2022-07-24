"""
Download all publicly available and linked PDF documents from one domain.
"""
import ssl
import certifi
import hashlib
import json
import os
import shutil
import sys
from io import BytesIO
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup  # pip install bs4


def md5(f):
    hash_md5 = hashlib.md5()
    stream = BytesIO(f)
    for chunk in iter(lambda: stream.read(4096), b""):
        hash_md5.update(chunk)
    return hash_md5.hexdigest()


def standardize_url(url):
    # crop anchor
    if "?" in url:
        return url.split("?")[0]
    if "#" in url:
        return url.split("#")[0]
    return url


class Spider:
    SNAPSHOT_FILE = "spider-snapshot.json"

    def __init__(self, urls: List[str], required_prefix: str = ""):
        self.pending_urls = urls
        self.visited_urls: Set[str] = set()
        self.required_prefix = required_prefix
        self.stored_at: Dict[str, str] = {}
        self.skip_suffixes = [
            ".jpg",
            ".png",
            ".gif",
            ".css",
            ".csv",
            ".xls",
            ".log",
            ".ps",
            ".xmp",
        ]

    def get_url(self, target) -> Optional[str]:
        return self.stored_at.get(target)

    def crawl_loop(self):
        while self.pending_urls:
            url = self.pending_urls.pop()
            self.visited_urls.add(url)
            self.crawl_page(url)
            print(url)
            self.snapshot()

    def crawl_page(self, url: str):
        try:
            response = requests.get(url)
        except Exception as exc:
            print(f"FAILED with {url} due to {exc}")
            return
        if response.status_code == 200:

            if "content-type" not in response.headers:
                print(f"!! No content type: {url}")
                return
            if "text/html" in response.headers["content-type"]:
                self.get_links(url, response.text)
            elif "application/pdf" in response.headers["content-type"]:
                self.store_pdf(response.content, url)
            else:
                print((response.headers["content-type"], url))

    def is_parsing_target(self, url: str) -> bool:
        _, ext = os.path.splitext(url)
        skip_domains = [
            "youtube.com",
            "twitter.com",
            "google.com",
            "xing.com",
            "linkedin.com",
            "apple.com",
            "wordpress.com",
            "mediawiki.com",
            "facebook.com",
            "flickr.com",
            "creativecommons.org",
            "matomo.org",
            "github.com",  # here might actually be quite a lot of PDFs
        ]
        domain = urlparse(url).netloc  # with subdomain
        domain = ".".join(domain.split(".")[-2:])
        return (
            url not in self.visited_urls
            and url not in self.pending_urls
            and url.startswith(self.required_prefix)
            and not ext in self.skip_suffixes
            and domain not in skip_domains
        )

    def get_links(self, current_url, html_page):
        soup = BeautifulSoup(html_page, "lxml")

        for link in soup.findAll("a"):
            url = link.get("href")
            if not url:
                continue
            if not url.startswith("http"):
                url = urljoin(current_url, url)
            url = standardize_url(url)
            print(f"...{url}")

            if self.is_parsing_target(url):
                self.pending_urls.append(url)

    def store_pdf(self, content, url) -> None:
        _total, _used, free = shutil.disk_usage("/")
        free_gb = free / (2**30)
        if free_gb < 3:  # leave at least 3 GB
            print("out of disk space")
            sys.exit()

        # url_md5sum = hashlib.md5(url.encode('utf-8')).hexdigest()
        url_md5sum = md5(content)
        if not os.path.exists("pdf"):
            os.mkdir("pdf")
        target = f"pdf/{url_md5sum}.pdf"
        if target not in self.stored_at:
            self.stored_at[target] = url
        if os.path.exists(target):
            print(f"{target} already exists: Skip {url}")
            return None
        with open(target, "wb") as f:
            f.write(content)

    def snapshot(self):
        with open(Spider.SNAPSHOT_FILE, "w") as f:
            json.dump(
                {
                    "stored_at": self.stored_at,
                    "visited_urls": list(self.visited_urls),
                    "pending_urls": self.pending_urls,
                },
                f,
                indent=2,
            )

    def load(self):
        if os.path.exists(Spider.SNAPSHOT_FILE):
            with open(Spider.SNAPSHOT_FILE) as f:
                snapshot = json.load(f)
                self.pending_urls = snapshot["pending_urls"]
                self.visited_urls = set(snapshot["visited_urls"])
                self.stored_at = snapshot.get("stored_at", {})


if __name__ == "__main__":
    spider = Spider(
        ["https://corpora.tika.apache.org/base/docs/govdocs1/"],
        required_prefix="https://corpora.tika",
    )
    spider.load()
    spider.crawl_loop()
