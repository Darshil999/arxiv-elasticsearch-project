"""Check that the Qdrant collection is populated and that semantic search returns sensible results.

    python scripts/verify_index.py
    python scripts/verify_index.py "graph neural networks for molecules"
"""

import sys

from common import use_backend_package

use_backend_package()

from app.core.config import get_settings  # noqa: E402
from app.models.schemas import SearchRequest  # noqa: E402
from app.services.embedding import get_embedder  # noqa: E402
from app.services.search import semantic_search  # noqa: E402
from app.services.vector_store import get_vector_store  # noqa: E402

DEFAULT_QUERIES = [
    "transformer models for natural language processing",
    "detecting objects in images with deep learning",
    "consensus protocols for distributed systems",
]


def main() -> None:
    settings = get_settings()
    store = get_vector_store()

    if not store.collection_exists():
        raise SystemExit(f"Collection '{settings.qdrant_collection}' does not exist. Run seed_database.py first.")

    count = store.count()
    print(f"Collection '{settings.qdrant_collection}' at {settings.qdrant_url} holds {count:,} papers.")
    if count == 0:
        raise SystemExit("The collection is empty. Run seed_database.py.")

    embedder = get_embedder()
    for query in sys.argv[1:] or DEFAULT_QUERIES:
        response = semantic_search(SearchRequest(query=query, limit=3), embedder, store)
        print(f"\nQuery: {query}   ({response.took_ms} ms)")
        for hit in response.results:
            print(f"  [{hit.score:.3f}] {hit.title}  ({hit.arxiv_id}, {hit.primary_category})")

    print("\nOK - the index is populated and searchable.")


if __name__ == "__main__":
    main()
