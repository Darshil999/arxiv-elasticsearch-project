"""Download recent paper metadata straight from the public arXiv API (no account needed).

This is the quickest way to build the demo dataset:

    python scripts/fetch_arxiv.py --total 20000

It pulls the most recently submitted papers from each category in DEFAULT_CATEGORIES,
de-duplicates cross-listed papers and writes data/papers.jsonl.

The arXiv API asks clients to wait ~3 seconds between requests, so 20,000 papers takes
roughly 2-4 minutes. See https://info.arxiv.org/help/api/user-manual.html
"""

import argparse
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import httpx

from common import DEFAULT_CATEGORIES, DEFAULT_PAPERS_FILE, make_record, write_jsonl

API_URL = "https://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
REQUEST_DELAY_S = 3.0
MAX_RETRIES = 5


def parse_feed(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    records = []
    for entry in root.findall("atom:entry", NS):
        abs_url = entry.findtext("atom:id", default="", namespaces=NS)
        if "/abs/" not in abs_url:  # error entries have no /abs/ id
            continue
        categories = [c.attrib["term"] for c in entry.findall("atom:category", NS)]
        primary = entry.find("arxiv:primary_category", NS)
        records.append(
            make_record(
                arxiv_id=abs_url.split("/abs/", 1)[1],
                title=entry.findtext("atom:title", default="", namespaces=NS),
                abstract=entry.findtext("atom:summary", default="", namespaces=NS),
                authors=[a.findtext("atom:name", default="", namespaces=NS) for a in entry.findall("atom:author", NS)],
                categories=categories,
                primary_category=primary.attrib.get("term") if primary is not None else None,
                published=entry.findtext("atom:published", default="", namespaces=NS)[:10] or None,
                updated=entry.findtext("atom:updated", default="", namespaces=NS)[:10] or None,
            )
        )
    return records


def fetch_page(client: httpx.Client, category: str, start: int, size: int) -> list[dict]:
    params = {
        "search_query": f"cat:{category}",
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "start": start,
        "max_results": size,
    }
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.get(API_URL, params=params)
            response.raise_for_status()
            records = parse_feed(response.text)
            if records:
                return records
            # The arXiv API occasionally returns an empty page under load; retrying helps.
        except (httpx.HTTPError, ET.ParseError) as exc:
            print(f"    attempt {attempt} failed: {exc}")
        time.sleep(REQUEST_DELAY_S * attempt)
    return []


def fetch_category(client: httpx.Client, category: str, wanted: int, page_size: int) -> list[dict]:
    papers: list[dict] = []
    start = 0
    while len(papers) < wanted:
        size = min(page_size, wanted - len(papers))
        page = fetch_page(client, category, start, size)
        if not page:
            print(f"    no more results for {category} at offset {start}")
            break
        papers.extend(page)
        start += len(page)
        print(f"    {category}: {len(papers):>6,}/{wanted:,}")
        time.sleep(REQUEST_DELAY_S)
    return papers


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--total", type=int, default=20_000, help="Approximate number of papers (default 20000).")
    parser.add_argument("--categories", nargs="+", default=DEFAULT_CATEGORIES, help="arXiv categories to pull.")
    parser.add_argument("--page-size", type=int, default=1000, help="Results per API request (max 2000).")
    parser.add_argument("--out", type=Path, default=DEFAULT_PAPERS_FILE, help="Output JSONL file.")
    args = parser.parse_args()

    per_category = max(1, args.total // len(args.categories))
    print(f"Fetching ~{per_category:,} recent papers from each of {len(args.categories)} categories...")

    by_id: dict[str, dict] = {}
    with httpx.Client(timeout=60, headers={"User-Agent": "arxiv-semantic-search/1.0"}) as client:
        for category in args.categories:
            print(f"  -> {category}")
            for paper in fetch_category(client, category, per_category, args.page_size):
                if paper["title"] and paper["abstract"]:
                    by_id.setdefault(paper["arxiv_id"], paper)

    papers = sorted(by_id.values(), key=lambda p: p["published"] or "", reverse=True)
    n = write_jsonl(papers, args.out)
    print(f"\nWrote {n:,} unique papers to {args.out}")


if __name__ == "__main__":
    main()
