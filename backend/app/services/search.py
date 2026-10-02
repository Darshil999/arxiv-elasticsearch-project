"""Semantic search: embed the query, find the nearest papers in Qdrant."""

import time

from app.models.schemas import SearchRequest, SearchResponse, SearchResult
from app.services.embedding import Embedder
from app.services.vector_store import VectorStore


def semantic_search(request: SearchRequest, embedder: Embedder, store: VectorStore) -> SearchResponse:
    started = time.perf_counter()

    query_vector = embedder.embed_query(request.query)
    hits = store.search(query_vector, limit=request.limit, categories=request.categories)

    results = [SearchResult(score=round(hit.score, 4), **(hit.payload or {})) for hit in hits]
    took_ms = round((time.perf_counter() - started) * 1000, 1)
    return SearchResponse(query=request.query, count=len(results), took_ms=took_ms, results=results)
