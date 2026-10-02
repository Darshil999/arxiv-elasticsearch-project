"""Embed papers and upload them to Qdrant.

    python scripts/seed_database.py                          # data/papers.jsonl, or the bundled sample
    python scripts/seed_database.py --file data/sample/papers.jsonl
    python scripts/seed_database.py --recreate               # drop and rebuild the collection

Reads connection settings from the same environment variables as the API
(QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION), so pointing it at Qdrant Cloud
only requires a filled-in .env file.

For each batch it builds "title. abstract", embeds it with all-MiniLM-L6-v2 (384 dims)
and upserts the vector + metadata. Point ids are derived from the arXiv id, so
re-running the script updates papers instead of duplicating them.
"""

import argparse
import time
from itertools import islice
from pathlib import Path

from tqdm import tqdm

from common import DEFAULT_PAPERS_FILE, SAMPLE_PAPERS_FILE, read_jsonl, use_backend_package

use_backend_package()

from app.core.config import get_settings  # noqa: E402
from app.services.embedding import get_embedder, paper_text  # noqa: E402
from app.services.vector_store import get_vector_store  # noqa: E402


def batched(iterable, size):
    iterator = iter(iterable)
    while batch := list(islice(iterator, size)):
        yield batch


def wait_for_qdrant(store, timeout_s: int = 60) -> None:
    """Qdrant may still be booting (e.g. right after `docker compose up`)."""
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            store.ping()
            return
        except Exception as exc:  # noqa: BLE001
            if time.monotonic() > deadline:
                raise SystemExit(f"Could not connect to Qdrant: {exc}") from exc
            print("Waiting for Qdrant ...")
            time.sleep(2)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", type=Path, default=None, help="JSONL file of papers to index.")
    parser.add_argument("--batch-size", type=int, default=256, help="Papers embedded + uploaded per batch.")
    parser.add_argument("--limit", type=int, default=0, help="Only index the first N papers (0 = all).")
    parser.add_argument("--recreate", action="store_true", help="Delete and recreate the collection first.")
    parser.add_argument("--if-empty", action="store_true", help="Do nothing if the collection already has papers.")
    args = parser.parse_args()

    path = args.file or (DEFAULT_PAPERS_FILE if DEFAULT_PAPERS_FILE.exists() else SAMPLE_PAPERS_FILE)
    if not path.exists():
        raise SystemExit(f"Papers file not found: {path}. Run scripts/fetch_arxiv.py first.")

    settings = get_settings()
    print(f"Qdrant:     {settings.qdrant_url}  (collection '{settings.qdrant_collection}')")
    print(f"Input file: {path}")

    store = get_vector_store()
    wait_for_qdrant(store)
    store.ensure_collection(recreate=args.recreate)

    if args.if_empty and (existing := store.count()) > 0:
        print(f"Collection already holds {existing:,} papers; skipping (--if-empty).")
        return

    papers = list(read_jsonl(path))
    if args.limit:
        papers = papers[: args.limit]

    print(f"Loading embedding model {settings.embedding_model} ...")
    embedder = get_embedder()

    started = time.perf_counter()
    with tqdm(total=len(papers), unit=" papers", desc="Indexing") as progress:
        for batch in batched(papers, args.batch_size):
            vectors = embedder.embed_documents(paper_text(p["title"], p["abstract"]) for p in batch)
            store.upsert(batch, vectors)
            progress.update(len(batch))

    elapsed = time.perf_counter() - started
    print(f"\nIndexed {len(papers):,} papers in {elapsed:.0f}s. Collection now holds {store.count():,} papers.")
    print("Verify with: python scripts/verify_index.py")


if __name__ == "__main__":
    main()
