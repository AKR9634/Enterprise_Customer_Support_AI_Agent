"""
Singleton wrapper around a HuggingFace sentence-transformers model.

Exposes embed() and embed_batch() and caches the model at module level
so that importers (ingest.py, retriever.py) share a single model instance.
"""

from functools import lru_cache
from typing import Optional

import numpy as np
from numpy.typing import NDArray
from sentence_transformers import SentenceTransformer

from app.config import EMBEDDING_MODEL


@lru_cache(maxsize=1)
def _load_model(model_name: Optional[str] = None) -> SentenceTransformer:
    return SentenceTransformer(model_name or EMBEDDING_MODEL)


def get_model() -> SentenceTransformer:
    return _load_model()


def embed(text: str) -> list[float]:
    model = get_model()
    vec: NDArray[np.float32] = model.encode(text, normalize_embeddings=True)
    return vec.tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    model = get_model()
    vecs: NDArray[np.float32] = model.encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vecs]
