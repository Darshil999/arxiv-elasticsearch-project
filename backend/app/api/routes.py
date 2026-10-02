"""HTTP routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.models.schemas import HealthResponse, SearchRequest, SearchResponse, StatsResponse
from app.services.embedding import EMBEDDING_DIM, Embedder, get_embedder
from app.services.search import semantic_search
from app.services.vector_store import VectorStore, VectorStoreError, get_vector_store

logger = logging.getLogger(__name__)

router = APIRouter()

_DB_UNAVAILABLE = "The vector database is unavailable. Please try again shortly."


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health(store: VectorStore = Depends(get_vector_store)) -> JSONResponse:
    """Liveness + dependency check. Returns 503 if Qdrant is unreachable or the collection is missing."""
    try:
        papers = store.count()
    except Exception as exc:  # noqa: BLE001 - any failure means "unhealthy"
        logger.warning("Health check failed: %s", exc)
        body = HealthResponse(status="degraded", vector_db="unreachable", detail=str(exc)[:200])
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=body.model_dump())
    return JSONResponse(content=HealthResponse(status="ok", vector_db="ok", papers_indexed=papers).model_dump())


@router.get("/api/stats", response_model=StatsResponse, tags=["search"])
def stats(store: VectorStore = Depends(get_vector_store)) -> StatsResponse:
    """Size of the indexed corpus and the embedding model in use."""
    try:
        count = store.count()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Stats query failed")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, _DB_UNAVAILABLE) from exc
    settings = get_settings()
    return StatsResponse(
        papers_indexed=count,
        embedding_model=settings.embedding_model,
        embedding_dim=EMBEDDING_DIM,
        collection=settings.qdrant_collection,
    )


@router.post("/api/search", response_model=SearchResponse, tags=["search"])
def search(
    request: SearchRequest,
    embedder: Embedder = Depends(get_embedder),
    store: VectorStore = Depends(get_vector_store),
) -> SearchResponse:
    """Find the papers whose title + abstract are semantically closest to the query."""
    try:
        return semantic_search(request, embedder, store)
    except VectorStoreError as exc:
        logger.exception("Qdrant returned an error")
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "The paper index has not been created yet. Run scripts/seed_database.py.",
            ) from exc
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, _DB_UNAVAILABLE) from exc
    except Exception as exc:  # noqa: BLE001 - network errors, timeouts, etc.
        logger.exception("Search failed")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, _DB_UNAVAILABLE) from exc
