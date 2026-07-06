"""
Embeds a query and runs a filtered similarity search against
Qdrant's knowledge_base collection, returning ranked chunks with
their source titles for citation.
"""

import logging
from typing import Any

from qdrant_client import QdrantClient

from app.config import QDRANT_API_KEY, QDRANT_COLLECTION, QDRANT_URL
from app.rag.embedder import embed

logger = logging.getLogger(__name__)


def _get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)


def search(
    query_text: str,
    top_k: int = 5,
    collection_name: str | None = None,
) -> list[dict[str, Any]]:
    collection = collection_name or QDRANT_COLLECTION
    query_vector = embed(query_text)

    client = _get_qdrant_client()
    result = client.query_points(
        collection_name=collection,
        query=query_vector,
        limit=top_k * 3,
        with_payload=True,
        score_threshold=0.55,
    )

    scored: list[dict[str, Any]] = []
    for point in result.points:
        payload = point.payload or {}
        scored.append({
            "source": payload.get("source", ""),
            "section": payload.get("section", ""),
            "chunk_index": payload.get("chunk_index", 0),
            "text": payload.get("text", ""),
            "score": point.score,
        })

    seen: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in scored:
        key = (entry["source"], entry["section"])
        if key not in seen or entry["score"] > seen[key]["score"]:
            seen[key] = entry

    results = sorted(seen.values(), key=lambda x: x["score"], reverse=True)
    return results[:top_k]
