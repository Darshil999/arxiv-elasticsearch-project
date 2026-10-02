"""Application settings, loaded from environment variables (and an optional .env file)."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Vector database (Qdrant) ---
    qdrant_url: str = Field(
        default="http://127.0.0.1:6333",
        description="Qdrant endpoint. Qdrant Cloud URL in production, http://qdrant:6333 in Docker.",
    )
    qdrant_api_key: str | None = Field(default=None, description="Qdrant Cloud API key (unset for local Qdrant).")
    qdrant_collection: str = "arxiv_papers"

    # --- Embeddings ---
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_cache_dir: str | None = Field(
        default=None, description="Where the ONNX model files are cached. Baked into the Docker image."
    )
    embedding_threads: int | None = Field(
        default=None,
        description="ONNX Runtime threads. Use 1 on small shared CPUs (free tiers); unset = all cores.",
    )

    # --- API ---
    # Comma-separated list of browser origins allowed to call the API.
    frontend_url: str = "http://localhost:3000"
    max_results: int = 50

    @field_validator("qdrant_api_key", "embedding_cache_dir", "embedding_threads", mode="before")
    @classmethod
    def _blank_to_none(cls, value: str | None) -> str | None:
        return value or None

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.frontend_url.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
