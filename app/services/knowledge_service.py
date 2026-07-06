"""
search(query_text) — embeds the query, retrieves matching chunks
from Qdrant via the retriever, dedupes/re-ranks them, and assembles
a token-budgeted, citation-formatted context string.
"""

import logging

from app.rag import retriever

logger = logging.getLogger(__name__)


class KnowledgeService:

    @staticmethod
    def search(query_text: str, max_tokens: int = 1500) -> str:
        chunks = retriever.search(query_text)
        if not chunks:
            return ""

        parts: list[str] = []
        token_count = 0

        for chunk in chunks:
            header = f"[Source: {chunk['source']} \u2014 {chunk['section']}]"
            body = chunk["text"]
            estimated = (len(header) + len(body) + 4) // 4
            if token_count + estimated > max_tokens:
                remaining = max_tokens - token_count
                if remaining > 0:
                    header_est = (len(header) + 2) // 4
                    if header_est < remaining:
                        body_max_chars = remaining * 4 - len(header) - 2
                        truncated = body[:body_max_chars]
                        parts.append(f"{header}\n\n{truncated}")
                break

            parts.append(f"{header}\n\n{body}")
            token_count += estimated

        return "\n\n---\n\n".join(parts)
