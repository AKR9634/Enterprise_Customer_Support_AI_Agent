"""Unit tests for RouteNode.

Verifies the node calls LLMClient.generate with the supervisor prompt
and writes active_agent and routing_reason to state.
"""

from unittest.mock import MagicMock

import pytest

from app.graph.nodes.route import RouteNode


class TestRouteNode:

    def test_routes_billing_when_llm_returns_billing(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "billing"
        node = RouteNode(llm=mock_llm)

        result = node({
            "category": "billing",
            "retrieved_docs": [
                {"source": "billing_policy.md", "text": "Refund policy"},
            ],
        })

        assert result["active_agent"] == "billing"
        assert "billing" in result["routing_reason"]

    def test_routes_order_when_llm_returns_order(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "order"
        node = RouteNode(llm=mock_llm)

        result = node({
            "category": "order",
            "retrieved_docs": [],
        })

        assert result["active_agent"] == "order"

    def test_routes_general_when_category_general(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "general"
        node = RouteNode(llm=mock_llm)

        result = node({
            "category": "general",
            "retrieved_docs": None,
        })

        assert result["active_agent"] == "general"
        assert "general" in result["routing_reason"]

    def test_strips_extra_whitespace_from_llm_output(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "  account\n"
        node = RouteNode(llm=mock_llm)

        result = node({
            "category": "account",
            "retrieved_docs": [],
        })

        assert result["active_agent"] == "account"

    def test_strips_quotes_from_llm_output(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = '"product"'
        node = RouteNode(llm=mock_llm)

        result = node({
            "category": "product",
            "retrieved_docs": [],
        })

        assert result["active_agent"] == "product"

    def test_falls_back_to_general_for_invalid_specialist(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "refund-specialist"
        node = RouteNode(llm=mock_llm)

        result = node({
            "category": "billing",
            "retrieved_docs": [],
        })

        assert result["active_agent"] == "general"

    def test_category_only_routing_when_no_retrieved_docs(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "billing"
        node = RouteNode(llm=mock_llm)

        result = node({
            "category": "billing",
            "retrieved_docs": None,
        })

        assert result["active_agent"] == "billing"
        assert "Category: billing" in result["routing_reason"]

    def test_only_writes_own_fields(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "order"
        node = RouteNode(llm=mock_llm)

        result = node({
            "category": "order",
            "retrieved_docs": [],
            "ticket_id": "t-1",
            "customer_message": "Where is my order",
            "escalate": False,
        })

        assert set(result.keys()) == {"active_agent", "routing_reason"}

    def test_context_summary_includes_doc_sources(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "billing"
        node = RouteNode(llm=mock_llm)

        result = node({
            "category": "billing",
            "retrieved_docs": [
                {"source": "billing_policy.md", "section": "Refunds", "text": "Refund policy"},
                {"source": "faq.md", "section": "", "text": "Common questions"},
            ],
        })

        assert result["routing_reason"] == "Category: billing, context confirms billing issue"

    def test_routes_account_when_llm_returns_account(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "account"
        node = RouteNode(llm=mock_llm)

        result = node({
            "category": "account",
            "retrieved_docs": [],
        })

        assert result["active_agent"] == "account"

    def test_routes_product_when_llm_returns_product(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "product"
        node = RouteNode(llm=mock_llm)

        result = node({
            "category": "product",
            "retrieved_docs": [],
        })

        assert result["active_agent"] == "product"
