"""Sentence embeddings with all-MiniLM-L6-v2, run directly on ONNX Runtime.

This reproduces sentence-transformers' pipeline (WordPiece tokenisation, 256-token
truncation, mean pooling over the attention mask, L2 normalisation) without PyTorch.
It produces the same 384-dim vectors while using ~200 MB of RAM and importing quickly,
which is what lets the API run and cold-start on a free 0.1-CPU / 512 MB instance.

The model files come from the official Hugging Face repo and are cached locally:

    python -m app.services.embedding        # pre-download (done in the Docker build)
"""

import logging
import threading
import time
from collections.abc import Iterable
from pathlib import Path

import httpx
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

from app.core.config import get_settings

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 384
MAX_TOKENS = 256  # sentence-transformers' max_seq_length for this model

_MODEL_FILES = {"model.onnx": "onnx/model.onnx", "tokenizer.json": "tokenizer.json"}
_DEFAULT_CACHE = Path(__file__).resolve().parents[2] / "model-cache"


def model_dir(model_name: str, cache_dir: str | None) -> Path:
    return Path(cache_dir or _DEFAULT_CACHE) / model_name.replace("/", "--")


def download_model(model_name: str, cache_dir: str | None = None) -> Path:
    """Fetch the ONNX weights + tokenizer from Hugging Face if they are not cached yet."""
    target = model_dir(model_name, cache_dir)
    target.mkdir(parents=True, exist_ok=True)
    for local_name, remote_path in _MODEL_FILES.items():
        path = target / local_name
        if path.exists():
            continue
        url = f"https://huggingface.co/{model_name}/resolve/main/{remote_path}"
        _download(url, path)
    return target


def _download(url: str, path: Path, attempts: int = 4) -> None:
    tmp = path.with_suffix(".part")
    for attempt in range(1, attempts + 1):
        logger.info("Downloading %s (attempt %d)", url, attempt)
        try:
            with httpx.stream("GET", url, follow_redirects=True, timeout=120) as response:
                response.raise_for_status()
                with tmp.open("wb") as f:
                    for chunk in response.iter_bytes():
                        f.write(chunk)
            tmp.replace(path)
            return
        except httpx.HTTPError as exc:
            if attempt == attempts:
                raise RuntimeError(f"Could not download {url}: {exc}") from exc
            time.sleep(2**attempt)


class Embedder:
    def __init__(self, model_name: str, cache_dir: str | None = None, threads: int | None = None) -> None:
        self.model_name = model_name
        files = download_model(model_name, cache_dir)

        self._tokenizer = Tokenizer.from_file(str(files / "tokenizer.json"))
        self._tokenizer.enable_truncation(max_length=MAX_TOKENS)
        self._tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")

        options = ort.SessionOptions()
        if threads:
            options.intra_op_num_threads = threads
            options.inter_op_num_threads = 1
        self._session = ort.InferenceSession(
            str(files / "model.onnx"), sess_options=options, providers=["CPUExecutionProvider"]
        )
        self._input_names = {i.name for i in self._session.get_inputs()}

    def _encode(self, texts: list[str]) -> np.ndarray:
        encodings = self._tokenizer.encode_batch(texts)
        input_ids = np.array([e.ids for e in encodings], dtype=np.int64)
        attention_mask = np.array([e.attention_mask for e in encodings], dtype=np.int64)
        feeds = {"input_ids": input_ids, "attention_mask": attention_mask}
        if "token_type_ids" in self._input_names:
            feeds["token_type_ids"] = np.zeros_like(input_ids)

        token_embeddings = self._session.run(None, feeds)[0]  # (batch, seq, dim)

        # Mean pooling over real (non-padding) tokens, then L2 normalisation.
        mask = attention_mask[..., None].astype(np.float32)
        pooled = (token_embeddings * mask).sum(axis=1) / np.clip(mask.sum(axis=1), 1e-9, None)
        return pooled / np.clip(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-12, None)

    def embed_query(self, text: str) -> list[float]:
        return self._encode([text])[0].tolist()

    def embed_documents(self, texts: Iterable[str], batch_size: int = 16) -> list[np.ndarray]:
        texts = list(texts)
        vectors: list[np.ndarray] = []
        for start in range(0, len(texts), batch_size):
            vectors.extend(self._encode(texts[start : start + batch_size]))
        return vectors


_embedder: Embedder | None = None
_embedder_lock = threading.Lock()


def get_embedder() -> Embedder:
    """Process-wide model instance. Thread-safe: the API warms it up in a background thread."""
    global _embedder
    if _embedder is None:
        with _embedder_lock:
            if _embedder is None:
                settings = get_settings()
                _embedder = Embedder(settings.embedding_model, settings.embedding_cache_dir, settings.embedding_threads)
    return _embedder


def paper_text(title: str, abstract: str) -> str:
    """Text that gets embedded for each paper (same recipe as the original Elasticsearch pipeline)."""
    return f"{title.strip()}. {abstract.strip()}"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    path = download_model(settings.embedding_model, settings.embedding_cache_dir)
    print(f"Model files ready in {path}")
