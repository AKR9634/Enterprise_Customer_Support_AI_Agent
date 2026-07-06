"""Unit tests for RetrieveNode.

Verifies the node calls retriever.search and writes retrieved_docs
as a list of structured dicts without mutating other state fields.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.graph.nodes.retrieve import RetrieveNode


def _chunk(
    source: str = "faq.md",
    section: str = "Returns",
    text: str = "30 day return policy",
    score: float = 0.92,
    chunk_index: int = 0,
) -> dict:
    return {
        "source": source,
        "section": section,
        "chunk_index": chunk_index,
        "text": text,
        "score": score,
    }


class TestRetrieveNode:

    def test_calls_retriever_and_formats_docs(self) -> None:
        with patch("app.graph.nodes.retrieve.retriever.search") as mock_search:
            mock_search.return_value = [
                _chunk("faq.md", "Returns", "30 day policy", 0.92),
                _chunk("billing.md", "Pricing", "$19/month", 0.88),
            ]
            node = RetrieveNode()

            result = node({"customer_message": "return policy"})

        assert result == {
            "retrieved_docs": [
                {"source": "faq.md", "section": "Returns", "text": "30 day policy", "score": 0.92},
                {"source": "billing.md", "section": "Pricing", "text": "$19/month", "score": 0.88},
            ]
        }
        mock_search.assert_called_once_with("return policy")

    def test_only_writes_own_field(self) -> None:
        with patch("app.graph.nodes.retrieve.retriever.search", return_value=[]):
            node = RetrieveNode()

            result = node({
                "customer_message": "test",
                "ticket_id": "t-1",
                "category": "general",
            })

        assert set(result.keys()) == {"retrieved_docs"}

    def test_empty_message_returns_empty_docs(self) -> None:
        node = RetrieveNode()

        result = node({"customer_message": ""})

        assert result == {"retrieved_docs": []}

    def test_no_message_returns_empty_docs(self) -> None:
        node = RetrieveNode()

        result = node({})

        assert result == {"retrieved_docs": []}

    def test_excludes_chunk_index_from_output(self) -> None:
        with patch("app.graph.nodes.retrieve.retriever.search") as mock_search:
            mock_search.return_value = [
                _chunk("faq.md", "FAQ", "Some text", 0.95, chunk_index=3),
            ]
            node = RetrieveNode()

            result = node({"customer_message": "help"})

        doc = result["retrieved_docs"][0]
        assert "chunk_index" not in doc
        assert list(doc.keys()) == ["source", "section", "text", "score"]
