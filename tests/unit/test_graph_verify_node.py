"""Unit tests for VerifyNode.

Verifies the node calls LLMClient.generate with a verification prompt
and only writes grounding_ok (bool).
"""

from unittest.mock import MagicMock, patch

import pytest

from app.graph.nodes.verify import VerifyNode


class TestVerifyNode:

    def test_returns_true_when_llm_says_yes(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "YES"
        node = VerifyNode(llm=mock_llm)

        result = node({
            "draft_response": "Refunds are available within 30 days.",
            "retrieved_docs": [
                {"source": "refund_policy.md", "text": "Refunds are available within 30 days."},
            ],
            "business_data": {},
        })

        assert result == {"grounding_ok": True}

    def test_returns_false_when_llm_says_no(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "NO"
        node = VerifyNode(llm=mock_llm)

        result = node({
            "draft_response": "You can return items after 90 days.",
            "retrieved_docs": [
                {"source": "refund_policy.md", "text": "Refunds are available within 30 days."},
            ],
            "business_data": {},
        })

        assert result == {"grounding_ok": False}

    def test_only_writes_own_field(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "YES"
        node = VerifyNode(llm=mock_llm)

        result = node({
            "draft_response": "Hello",
            "retrieved_docs": [],
            "business_data": {},
            "ticket_id": "t-1",
            "category": "general",
        })

        assert set(result.keys()) == {"grounding_ok"}

    def test_empty_draft_returns_false(self) -> None:
        node = VerifyNode(llm=MagicMock())

        result = node({
            "draft_response": "",
            "retrieved_docs": [],
            "business_data": {},
        })

        assert result == {"grounding_ok": False}

    def test_no_docs_returns_false(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "NO"
        node = VerifyNode(llm=mock_llm)

        result = node({
            "draft_response": "Some claim without sources.",
            "retrieved_docs": [],
            "business_data": {},
        })

        assert result == {"grounding_ok": False}

    def test_yes_with_extra_text(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "YES, all claims are supported."
        node = VerifyNode(llm=mock_llm)

        result = node({
            "draft_response": "Our policy allows refunds.",
            "retrieved_docs": [
                {"source": "policy.md", "text": "Refunds allowed."},
            ],
            "business_data": {},
        })

        assert result == {"grounding_ok": True}
