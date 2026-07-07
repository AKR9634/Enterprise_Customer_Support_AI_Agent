"""Unit tests for ClassifyNode.

Verifies the node calls LLMClient.classify with the correct arguments
and only writes the fields it owns (category, intent_confidence).
"""

from unittest.mock import MagicMock, patch

import pytest

from app.graph.nodes.classify import CATEGORIES, ClassifyNode


class TestClassifyNode:

    def test_calls_llm_classify_and_writes_category(self) -> None:
        mock_llm = MagicMock()
        mock_llm.classify.return_value = "billing"
        node = ClassifyNode(llm=mock_llm)

        result = node({"customer_message": "I want a refund"})

        assert result == {"category": "billing", "intent_confidence": 0.95}
        mock_llm.classify.assert_called_once_with("I want a refund", CATEGORIES)

    def test_only_writes_own_fields(self) -> None:
        mock_llm = MagicMock()
        mock_llm.classify.return_value = "order"
        node = ClassifyNode(llm=mock_llm)

        result = node({
            "customer_message": "Where is my order",
            "ticket_id": "t-1",
            "escalate": False,
        })

        assert set(result.keys()) == {"category", "intent_confidence"}

    def test_empty_message_returns_none_values(self) -> None:
        node = ClassifyNode(llm=MagicMock())

        result = node({"customer_message": ""})

        assert result == {"category": None, "intent_confidence": None}

    def test_classifies_order_intent(self) -> None:
        mock_llm = MagicMock()
        mock_llm.classify.return_value = "order"
        node = ClassifyNode(llm=mock_llm)

        result = node({"customer_message": "Track my shipment"})

        assert result["category"] == "order"

    def test_classifies_general_intent(self) -> None:
        mock_llm = MagicMock()
        mock_llm.classify.return_value = "general"
        node = ClassifyNode(llm=mock_llm)

        result = node({"customer_message": "What are your hours"})

        assert result["category"] == "general"

    def test_classifies_account_intent(self) -> None:
        mock_llm = MagicMock()
        mock_llm.classify.return_value = "account"
        node = ClassifyNode(llm=mock_llm)

        result = node({"customer_message": "Reset my password"})

        assert result["category"] == "account"

    def test_classifies_product_intent(self) -> None:
        mock_llm = MagicMock()
        mock_llm.classify.return_value = "product"
        node = ClassifyNode(llm=mock_llm)

        result = node({"customer_message": "What are the specs"})

        assert result["category"] == "product"
