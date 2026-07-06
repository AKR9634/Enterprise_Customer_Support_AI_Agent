"""
Node 3 — Knowledge Retrieval. Embeds the customer's question and
calls the retriever to pull relevant, cited chunks from Qdrant into
retrieved_docs as a list of structured dicts.
"""

from __future__ import annotations

from app.graph.state import SupportState
from app.rag import retriever

__all__ = [
    "RetrieveNode",
]


class RetrieveNode:
    """Graph node that searches the knowledge base for chunks relevant
    to the customer message and writes them as structured dicts."""

    def __call__(self, state: SupportState) -> dict:
        message = state.get("customer_message", "")
        if not message:
            return {"retrieved_docs": []}

        chunks = retriever.search(message)
        docs = [
            {
                "source": ch["source"],
                "section": ch["section"],
                "text": ch["text"],
                "score": ch["score"],
            }
            for ch in chunks
        ]
        return {"retrieved_docs": docs}
