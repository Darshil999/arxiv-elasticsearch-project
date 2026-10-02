"""FastAPI entrypoint: `uvicorn app.main:app`."""

import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.services.embedding import get_embedder

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)  # qdrant-client logs every request otherwise
logger = logging.getLogger("arxiv-search")


def _warm_up_model() -> None:
    try:
        embedder = get_embedder()
        embedder.embed_query("warm up")
        logger.info("Embedding model ready: %s", embedder.model_name)
    except Exception:
        logger.exception("Failed to load the embedding model")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Load the model in the background so the server binds its port (and answers /health)
    # immediately. On small free-tier CPUs loading takes a while; a search that arrives
    # earlier simply waits for it.
    threading.Thread(target=_warm_up_model, name="model-warmup", daemon=True).start()
    yield


settings = get_settings()

app = FastAPI(
    title="ArXiv Semantic Search API",
    description="Discover research papers by meaning, not just keywords.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.include_router(router)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"name": "ArXiv Semantic Search API", "docs": "/docs", "health": "/health"}
