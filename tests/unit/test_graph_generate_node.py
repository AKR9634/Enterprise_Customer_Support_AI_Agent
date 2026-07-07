"""Unit tests for GenerateNode.

Verifies the node dispatches to the correct specialist agent based
on state["active_agent"], renders the prompt, calls LLMClient.generate,
and only writes draft_response.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.graph.nodes.generate import GenerateNode, _SPECIALIST_REGISTRY
from app.graph.agents.billing_agent import render_billing_prompt
from app.graph.agents.order_agent import render_order_prompt
from app.graph.agents.account_agent import render_account_prompt
from app.graph.agents.product_agent import render_product_prompt
from app.graph.agents.general_agent import render_general_prompt


class TestGenerateNode:

    def test_calls_llm_and_writes_draft(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "Thank you for reaching out."
        node = GenerateNode(llm=mock_llm)

        result = node({
            "customer_message": "I need help",
            "conversation_history": [],
            "retrieved_docs": [],
            "business_data": None,
        })

        assert result == {"draft_response": "Thank you for reaching out."}
        mock_llm.generate.assert_called_once()

    def test_only_writes_own_field(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "Sure, here is the info."
        node = GenerateNode(llm=mock_llm)

        result = node({
            "customer_message": "Tell me about refunds",
            "ticket_id": "t-1",
            "category": "general",
            "escalate": False,
        })

        assert set(result.keys()) == {"draft_response"}

    def test_empty_message_produces_some_draft(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "I'm not sure what you're asking."
        node = GenerateNode(llm=mock_llm)

        result = node({"customer_message": ""})

        assert "draft_response" in result
        mock_llm.generate.assert_called_once()

    def test_renders_prompt_with_context(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "Based on our policy..."
        node = GenerateNode(llm=mock_llm)

        result = node({
            "customer_message": "What is your refund policy?",
            "conversation_history": [
                {"role": "customer", "content": "I want a refund"},
            ],
            "retrieved_docs": [
                {"source": "refund_policy.md", "section": "Overview", "text": "Refunds are available within 30 days."},
            ],
            "business_data": {"order_total": "$50.00"},
        })

        assert result["draft_response"] == "Based on our policy..."
        call_args = mock_llm.generate.call_args[0][0]
        assert "Refunds are available within 30 days." in call_args
        assert "order_total" in call_args
        assert "I want a refund" in call_args

    def test_dispatch_billing(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "Billing reply."
        node = GenerateNode(llm=mock_llm)

        result = node({
            "customer_message": "My invoice is wrong",
            "active_agent": "billing",
        })

        assert result["draft_response"] == "Billing reply."
        call_args = mock_llm.generate.call_args[0][0]
        assert "billing specialist" in call_args.lower()

    def test_dispatch_order(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "Order reply."
        node = GenerateNode(llm=mock_llm)

        result = node({
            "customer_message": "Where is my order?",
            "active_agent": "order",
        })

        assert result["draft_response"] == "Order reply."
        call_args = mock_llm.generate.call_args[0][0]
        assert "order management" in call_args.lower()

    def test_dispatch_account(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "Account reply."
        node = GenerateNode(llm=mock_llm)

        result = node({
            "customer_message": "Reset my password",
            "active_agent": "account",
        })

        assert result["draft_response"] == "Account reply."
        call_args = mock_llm.generate.call_args[0][0]
        assert "account management" in call_args.lower()

    def test_dispatch_product(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "Product reply."
        node = GenerateNode(llm=mock_llm)

        result = node({
            "customer_message": "Tell me about the warranty",
            "active_agent": "product",
        })

        assert result["draft_response"] == "Product reply."
        call_args = mock_llm.generate.call_args[0][0]
        assert "product specialist" in call_args.lower()

    def test_dispatch_general(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "General reply."
        node = GenerateNode(llm=mock_llm)

        result = node({
            "customer_message": "I have a question",
            "active_agent": "general",
        })

        assert result["draft_response"] == "General reply."
        call_args = mock_llm.generate.call_args[0][0]
        assert "general customer support" in call_args.lower()

    def test_dispatch_falls_back_to_general(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "Fallback reply."
        node = GenerateNode(llm=mock_llm)

        result = node({
            "customer_message": "Help",
            "active_agent": "unknown-specialist",
        })

        assert result["draft_response"] == "Fallback reply."
        call_args = mock_llm.generate.call_args[0][0]
        assert "general customer support" in call_args.lower()

    def test_dispatch_defaults_to_general_when_no_active_agent(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "Default reply."
        node = GenerateNode(llm=mock_llm)

        result = node({
            "customer_message": "Help",
        })

        assert result["draft_response"] == "Default reply."
        call_args = mock_llm.generate.call_args[0][0]
        assert "general customer support" in call_args.lower()
