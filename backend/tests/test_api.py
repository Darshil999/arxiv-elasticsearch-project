"""API tests with the embedding model and Qdrant replaced by fakes (no network or model download)."""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.embedding import get_embedder
from app.services.vector_store import get_vector_store

PAPER = {
    "arxiv_id": "1706.03762",
    "title": "Attention Is All You Need",
    "abstract": "The dominant sequence transduction models are based on complex recurrent networks...",
    "authors": ["Ashish Vaswani", "Noam Shazeer"],
    "categories": ["cs.CL", "cs.LG"],
    "primary_category": "cs.CL",
    "published": "2017-06-12",
    "updated": "2023-08-02",
    "url": "https://arxiv.org/abs/1706.03762",
    "pdf_url": "https://arxiv.org/pdf/1706.03762",
}


class FakeEmbedder:
    model_name = "fake"

    def embed_query(self, text: str) -> list[float]:
        return [0.1] * 384


class FakeStore:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.last_call: dict | None = None

    def count(self) -> int:
        if self.fail:
            raise ConnectionError("qdrant down")
        return 1

    def search(self, vector, limit, categories=None):
        if self.fail:
            raise ConnectionError("qdrant down")
        self.last_call = {"limit": limit, "categories": categories}
        return [SimpleNamespace(score=0.83219, payload=PAPER)]


@pytest.fixture
def store():
    return FakeStore()


@pytest.fixture
def client(store):
    app.dependency_overrides[get_embedder] = lambda: FakeEmbedder()
    app.dependency_overrides[get_vector_store] = lambda: store
    # No `with` block: skip the lifespan hook so the real model is never loaded.
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_search_returns_ranked_papers(client, store):
    response = client.post("/api/search", json={"query": "  attention   models ", "limit": 5, "categories": ["cs.CL"]})
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "attention models"
    assert body["count"] == 1
    assert body["results"][0]["title"] == "Attention Is All You Need"
    assert body["results"][0]["score"] == 0.8322
    assert store.last_call == {"limit": 5, "categories": ["cs.CL"]}


@pytest.mark.parametrize(
    "payload",
    [{"query": ""}, {"query": " a "}, {"query": "ok query", "limit": 0}, {"query": "ok query", "limit": 51}, {}],
)
def test_search_validates_input(client, payload):
    assert client.post("/api/search", json=payload).status_code == 422


def test_search_reports_database_outage(client, store):
    store.fail = True
    response = client.post("/api/search", json={"query": "graph neural networks"})
    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"]


def test_health(client, store):
    assert client.get("/health").json() == {
        "status": "ok",
        "vector_db": "ok",
        "papers_indexed": 1,
        "detail": None,
    }
    store.fail = True
    assert client.get("/health").status_code == 503


def test_stats(client):
    body = client.get("/api/stats").json()
    assert body["papers_indexed"] == 1
    assert body["embedding_dim"] == 384


def test_cors_allows_configured_frontend(client):
    response = client.options(
        "/api/search",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"},
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

    blocked = client.options(
        "/api/search",
        headers={"Origin": "https://evil.example.com", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in blocked.headers
