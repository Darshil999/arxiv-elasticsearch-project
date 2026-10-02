"""Build the dataset from the full Kaggle arXiv snapshot (alternative to fetch_arxiv.py).

Download `arxiv-metadata-oai-snapshot.json` (~4.5 GB, NDJSON) from
https://www.kaggle.com/datasets/Cornell-University/arxiv and put it in data/, then:

    python scripts/prepare_data.py --limit 20000

The file is streamed line by line (constant memory). Papers are kept if they belong to
any of the selected categories, and the most recently submitted `--limit` papers are
written to data/papers.jsonl. Use `--categories cs` to keep every Computer Science paper
(the original course-project setup, ~850k papers), and `--limit 0` for no cap.
"""

import argparse
import heapq
import json
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

from common import DATA_DIR, DEFAULT_CATEGORIES, DEFAULT_PAPERS_FILE, make_record, write_jsonl

DEFAULT_SNAPSHOT = DATA_DIR / "arxiv-metadata-oai-snapshot.json"


def matches(categories: list[str], wanted: set[str]) -> bool:
    for category in categories:
        if category in wanted or category.split(".", 1)[0] in wanted:
            return True
    return False


def first_version_date(raw: dict) -> str | None:
    versions = raw.get("versions") or []
    if not versions:
        return None
    try:
        # e.g. "Mon, 2 Apr 2007 19:18:42 GMT"
        return datetime.strptime(versions[0]["created"], "%a, %d %b %Y %H:%M:%S %Z").strftime("%Y-%m-%d")
    except (KeyError, ValueError):
        return None


def to_record(raw: dict) -> dict | None:
    if not raw.get("title") or not raw.get("abstract"):
        return None
    categories = (raw.get("categories") or "").split()
    parsed = raw.get("authors_parsed") or []
    # authors_parsed entries are [last, first, suffix] -> "first last"
    authors = [" ".join(p for p in (a[1] if len(a) > 1 else "", a[0]) if p) for a in parsed if a] or [
        a.strip() for a in (raw.get("authors") or "").replace(" and ", ", ").split(",")
    ]
    return make_record(
        arxiv_id=raw["id"],
        title=raw["title"],
        abstract=raw["abstract"],
        authors=authors,
        categories=categories,
        primary_category=categories[0] if categories else None,
        published=first_version_date(raw) or raw.get("update_date"),
        updated=raw.get("update_date"),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT, help="Path to the Kaggle NDJSON snapshot.")
    parser.add_argument(
        "--categories",
        nargs="+",
        default=DEFAULT_CATEGORIES,
        help="Categories (cs.LG) or whole archives (cs) to keep.",
    )
    parser.add_argument("--limit", type=int, default=20_000, help="Keep the N most recent papers (0 = keep all).")
    parser.add_argument("--out", type=Path, default=DEFAULT_PAPERS_FILE, help="Output JSONL file.")
    args = parser.parse_args()

    if not args.snapshot.exists():
        raise SystemExit(f"Snapshot not found: {args.snapshot}\nDownload it from Kaggle (see docstring).")

    wanted = set(args.categories)
    seen = kept = 0
    heap: list[tuple[str, str, dict]] = []  # min-heap on published date -> keeps the newest N
    everything: list[dict] = []

    with args.snapshot.open(encoding="utf-8") as f:
        for line in tqdm(f, desc="Scanning snapshot", unit=" papers"):
            seen += 1
            raw = json.loads(line)
            if not matches((raw.get("categories") or "").split(), wanted):
                continue
            record = to_record(raw)
            if record is None:
                continue
            kept += 1
            if args.limit <= 0:
                everything.append(record)
            elif len(heap) < args.limit:
                heapq.heappush(heap, (record["published"] or "", record["arxiv_id"], record))
            else:
                heapq.heappushpop(heap, (record["published"] or "", record["arxiv_id"], record))

    papers = everything if args.limit <= 0 else [r for _, _, r in heap]
    papers.sort(key=lambda p: p["published"] or "", reverse=True)
    n = write_jsonl(papers, args.out)
    print(f"Scanned {seen:,} papers, {kept:,} matched {sorted(wanted)}.")
    print(f"Wrote {n:,} papers to {args.out}")


if __name__ == "__main__":
    main()
