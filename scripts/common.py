"""Shared helpers for the data scripts.

Every data source is normalised into the same JSON Lines record, one paper per line:

    {
      "arxiv_id": "2401.01234", "title": "...", "abstract": "...",
      "authors": ["Ada Lovelace", ...], "categories": ["cs.LG", "stat.ML"],
      "primary_category": "cs.LG", "published": "2024-01-02", "updated": "2024-02-10",
      "url": "https://arxiv.org/abs/2401.01234", "pdf_url": "https://arxiv.org/pdf/2401.01234"
    }
"""

import json
import re
import sys
from collections.abc import Iterable, Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DEFAULT_PAPERS_FILE = DATA_DIR / "papers.jsonl"
SAMPLE_PAPERS_FILE = DATA_DIR / "sample" / "papers.jsonl"

# A spread of popular CS areas so the demo covers a variety of topics.
DEFAULT_CATEGORIES = [
    "cs.AI",  # Artificial Intelligence
    "cs.CL",  # Computation and Language (NLP)
    "cs.CV",  # Computer Vision
    "cs.LG",  # Machine Learning
    "cs.IR",  # Information Retrieval
    "cs.DC",  # Distributed, Parallel, and Cluster Computing
    "cs.CR",  # Cryptography and Security
    "cs.RO",  # Robotics
]

_VERSION_SUFFIX = re.compile(r"v\d+$")


def use_backend_package() -> None:
    """Make `import app...` resolve to backend/app so scripts reuse the API's services."""
    backend = str(ROOT / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)


def clean_text(text: str | None) -> str:
    return " ".join((text or "").split())


def strip_version(arxiv_id: str) -> str:
    return _VERSION_SUFFIX.sub("", arxiv_id.strip())


def make_record(
    *,
    arxiv_id: str,
    title: str,
    abstract: str,
    authors: list[str],
    categories: list[str],
    primary_category: str | None,
    published: str | None,
    updated: str | None,
) -> dict:
    arxiv_id = strip_version(arxiv_id)
    return {
        "arxiv_id": arxiv_id,
        "title": clean_text(title),
        "abstract": clean_text(abstract),
        "authors": [clean_text(a) for a in authors if clean_text(a)],
        "categories": categories,
        "primary_category": primary_category or (categories[0] if categories else None),
        "published": published,
        "updated": updated,
        "url": f"https://arxiv.org/abs/{arxiv_id}",
        "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}",
    }


def write_jsonl(records: Iterable[dict], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            n += 1
    return n


def read_jsonl(path: Path) -> Iterator[dict]:
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)
