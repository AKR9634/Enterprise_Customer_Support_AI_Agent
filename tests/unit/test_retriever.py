"""
Unit tests for the retriever search function.

Mock QdrantClient and embed() so no network or model
download is required. Tests focus on search, dedup, and
threshold-filtering behaviour.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.rag.retriever import search


def _make_mock_point(
    score: float,
    source: str = "faq.md",
    section: str = "Returns",
    chunk_index: int = 0,
    text: str = "Some chunk text.",
) -> MagicMock:
    pt = MagicMock()
    pt.score = score
    pt.payload = {
        "source": source,
        "section": section,
        "chunk_index": chunk_index,
        "text": text,
    }
    return pt


class TestRetrieverSearch:

    @patch("app.rag.retriever._get_qdrant_client")
    @patch("app.rag.retriever.embed")
    def test_search_returns_ranked_results(
        self,
        mock_embed: MagicMock,
        mock_get_client: MagicMock,
    ) -> None:
        mock_embed.return_value = [0.1] * 384
        fake_client = MagicMock()
        fake_client.query_points.return_value.points = [
            _make_mock_point(0.85, section="Pricing"),
            _make_mock_point(0.95, section="Returns"),
            _make_mock_point(0.75, section="Shipping"),
        ]
        mock_get_client.return_value = fake_client

        results = search("test query", top_k=5)
        assert len(results) == 3
        assert results[0]["score"] >= results[1]["score"] >= results[2]["score"]
        assert all(k in results[0] for k in ("source", "section", "chunk_index", "text", "score"))

    @patch("app.rag.retriever._get_qdrant_client")
    @patch("app.rag.retriever.embed")
    def test_dedup_keeps_highest_score_per_section(
        self,
        mock_embed: MagicMock,
        mock_get_client: MagicMock,
    ) -> None:
        """Multiple chunks from same source+section — only the highest-score one is kept."""
        mock_embed.return_value = [0.1] * 384
        fake_client = MagicMock()
        fake_client.query_points.return_value.points = [
            _make_mock_point(0.70, source="faq.md", section="Returns", text="Low score"),
            _make_mock_point(0.95, source="faq.md", section="Returns", text="High score"),
            _make_mock_point(0.85, source="billing.md", section="Pricing", text="Different doc"),
        ]
        mock_get_client.return_value = fake_client

        results = search("test query", top_k=5)
        assert len(results) == 2  # dedup: faq.md/Returns appears once
        returns_chunk = [r for r in results if r["section"] == "Returns"]
        assert len(returns_chunk) == 1
        assert returns_chunk[0]["text"] == "High score"

    @patch("app.rag.retriever._get_qdrant_client")
    @patch("app.rag.retriever.embed")
    def test_score_threshold_passed_to_qdrant(
        self,
        mock_embed: MagicMock,
        mock_get_client: MagicMock,
    ) -> None:
        """verify that a score_threshold is passed to query_points."""
        mock_embed.return_value = [0.1] * 384
        fake_client = MagicMock()
        fake_client.query_points.return_value.points = []
        mock_get_client.return_value = fake_client

        search("anything")
        kwargs = fake_client.query_points.call_args.kwargs
        assert "score_threshold" in kwargs
        assert kwargs["score_threshold"] == 0.55

    @patch("app.rag.retriever._get_qdrant_client")
    @patch("app.rag.retriever.embed")
    def test_empty_results_when_no_points_returned(
        self,
        mock_embed: MagicMock,
        mock_get_client: MagicMock,
    ) -> None:
        mock_embed.return_value = [0.1] * 384
        fake_client = MagicMock()
        fake_client.query_points.return_value.points = []
        mock_get_client.return_value = fake_client

        results = search("empty query")
        assert results == []

    @patch("app.rag.retriever._get_qdrant_client")
    @patch("app.rag.retriever.embed")
    def test_respects_top_k(
        self,
        mock_embed: MagicMock,
        mock_get_client: MagicMock,
    ) -> None:
        """More unique sections than top_k are truncated."""
        mock_embed.return_value = [0.1] * 384
        fake_client = MagicMock()
        fake_client.query_points.return_value.points = [
            _make_mock_point(0.99, section="A"),
            _make_mock_point(0.98, section="B"),
            _make_mock_point(0.97, section="C"),
        ]
        mock_get_client.return_value = fake_client

        results = search("query", top_k=2)
        assert len(results) == 2

    @patch("app.rag.retriever._get_qdrant_client")
    @patch("app.rag.retriever.embed")
    def test_custom_collection_name(
        self,
        mock_embed: MagicMock,
        mock_get_client: MagicMock,
    ) -> None:
        mock_embed.return_value = [0.1] * 384
        fake_client = MagicMock()
        fake_client.query_points.return_value.points = []
        mock_get_client.return_value = fake_client

        search("query", collection_name="test_collection")
        kwargs = fake_client.query_points.call_args.kwargs
        assert kwargs["collection_name"] == "test_collection"
