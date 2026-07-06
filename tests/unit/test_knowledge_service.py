"""
Unit tests for KnowledgeService.search().

Mocks the retriever module so tests are fast and
deterministic.
"""

from unittest.mock import patch

import pytest

from app.services.knowledge_service import KnowledgeService


class TestKnowledgeServiceSearch:

    @patch("app.services.knowledge_service.retriever.search")
    def test_returns_formatted_citation_string(
        self,
        mock_retriever_search,
    ) -> None:
        mock_retriever_search.return_value = [
            _chunk("faq.md", "Returns", "You can return items within 30 days."),
            _chunk("billing.md", "Pricing", "Basic plan is $19/month."),
        ]

        result = KnowledgeService.search("refund policy")

        assert "[Source: faq.md \u2014 Returns]" in result
        assert "30 days" in result
        assert "[Source: billing.md \u2014 Pricing]" in result
        assert "$19/month" in result
        assert "---" in result

    @patch("app.services.knowledge_service.retriever.search")
    def test_empty_query_returns_empty_string(
        self,
        mock_retriever_search,
    ) -> None:
        mock_retriever_search.return_value = []

        result = KnowledgeService.search("nonexistent")
        assert result == ""

    @patch("app.services.knowledge_service.retriever.search")
    def test_respects_max_tokens_budget(
        self,
        mock_retriever_search,
    ) -> None:
        """Token budget truncation should drop/truncate chunks that exceed max_tokens."""
        mock_retriever_search.return_value = [
            _chunk("faq.md", "Long", "A" * 2000),
            _chunk("billing.md", "Short", "B" * 10),
        ]

        result = KnowledgeService.search("query", max_tokens=100)

        # With a 100 token budget (~400 chars), the long chunk alone will
        # exceed the budget, so the second chunk should not appear.
        assert "billing.md" not in result
        # The header should be present but body may be truncated
        assert "[Source: faq.md" in result

    @patch("app.services.knowledge_service.retriever.search")
    def test_result_format_is_markdown_friendly(
        self,
        mock_retriever_search,
    ) -> None:
        mock_retriever_search.return_value = [
            _chunk("faq.md", "FAQ", "Content."),
        ]

        result = KnowledgeService.search("query")
        lines = result.split("\n")
        assert lines[0] == "[Source: faq.md \u2014 FAQ]"
        assert lines[1] == ""
        assert lines[2] == "Content."

    @patch("app.services.knowledge_service.retriever.search")
    def test_chunks_separated_by_horizontal_rule(
        self,
        mock_retriever_search,
    ) -> None:
        mock_retriever_search.return_value = [
            _chunk("a.md", "A", "Chunk one"),
            _chunk("b.md", "B", "Chunk two"),
        ]

        result = KnowledgeService.search("query")
        assert "\n\n---\n\n" in result


def _chunk(source: str, section: str, text: str) -> dict:
    return {
        "source": source,
        "section": section,
        "chunk_index": 0,
        "text": text,
        "score": 0.95,
    }
