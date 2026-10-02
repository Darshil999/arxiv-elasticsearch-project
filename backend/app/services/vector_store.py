"""Qdrant access layer over its REST API: collection management, upserts and vector search.

Plain HTTP (httpx) instead of the qdrant-client SDK keeps the API's import time and memory
small, which matters for cold starts on free-tier hosts. Only a handful of endpoints are used:
https://api.qdrant.tech/api-reference
"""

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import httpx

from app.core.config import get_settings
from app.services.embedding import EMBEDDING_DIM

# Stable namespace so that re-indexing the same arXiv id overwrites the same point.
_POINT_NAMESPACE = uuid.UUID("5b0e1a62-4f4e-4d67-9c1f-1d3f6f3a9a11")


def point_id(arxiv_id: str) -> str:
    return str(uuid.uuid5(_POINT_NAMESPACE, arxiv_id))


class VectorStoreError(Exception):
    """Qdrant answered with an error status."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"Qdrant error {status_code}: {message}")
        self.status_code = status_code


@dataclass(frozen=True)
class ScoredPaper:
    score: float
    payload: dict[str, Any]


class VectorStore:
    def __init__(self, url: str, api_key: str | None, collection: str, timeout: float = 30) -> None:
        self.url = url.rstrip("/")
        self.collection = collection
        headers = {"api-key": api_key} if api_key else {}
        self._http = httpx.Client(base_url=self.url, headers=headers, timeout=timeout)

    def _request(self, method: str, path: str, json: Any = None) -> Any:
        response = self._http.request(method, path, json=json)
        if response.is_error:
            try:
                message = response.json().get("status", {}).get("error", response.text)
            except ValueError:
                message = response.text
            raise VectorStoreError(response.status_code, message[:300])
        return response.json().get("result")

    # ---- schema -----------------------------------------------------------------

    def ping(self) -> None:
        self._request("GET", "/collections")

    def collection_exists(self) -> bool:
        return bool(self._request("GET", f"/collections/{self.collection}/exists")["exists"])

    def ensure_collection(self, recreate: bool = False) -> None:
        """Create the collection (cosine distance, 384 dims) and payload indexes if missing."""
        exists = self.collection_exists()
        if exists and recreate:
            self._request("DELETE", f"/collections/{self.collection}")
            exists = False
        if not exists:
            self._request(
                "PUT",
                f"/collections/{self.collection}",
                {"vectors": {"size": EMBEDDING_DIM, "distance": "Cosine"}},
            )
        # Keyword indexes make category filtering fast; creating them twice is a no-op.
        for field in ("categories", "primary_category"):
            self._request(
                "PUT",
                f"/collections/{self.collection}/index?wait=true",
                {"field_name": field, "field_schema": "keyword"},
            )

    # ---- writes -----------------------------------------------------------------

    def upsert(self, payloads: Sequence[dict[str, Any]], vectors: Sequence[Sequence[float]]) -> None:
        points = [
            {"id": point_id(p["arxiv_id"]), "vector": [float(x) for x in v], "payload": p}
            for p, v in zip(payloads, vectors, strict=True)
        ]
        self._request("PUT", f"/collections/{self.collection}/points?wait=true", {"points": points})

    # ---- reads ------------------------------------------------------------------

    def count(self) -> int:
        return int(self._request("POST", f"/collections/{self.collection}/points/count", {"exact": True})["count"])

    def search(self, vector: list[float], limit: int, categories: list[str] | None = None) -> list[ScoredPaper]:
        body: dict[str, Any] = {"query": vector, "limit": limit, "with_payload": True}
        if categories:
            body["filter"] = {"must": [{"key": "categories", "match": {"any": categories}}]}
        result = self._request("POST", f"/collections/{self.collection}/points/query", body)
        return [ScoredPaper(score=p["score"], payload=p.get("payload") or {}) for p in result["points"]]


@lru_cache
def get_vector_store() -> VectorStore:
    settings = get_settings()
    return VectorStore(settings.qdrant_url, settings.qdrant_api_key, settings.qdrant_collection)
