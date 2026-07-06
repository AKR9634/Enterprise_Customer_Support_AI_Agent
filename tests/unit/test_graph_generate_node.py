"""Unit tests for GenerateNode.

Verifies the node renders the prompt via render_generic_agent_prompt,
calls LLMClient.generate, and only writes draft_response.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.graph.nodes.generate import GenerateNode


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
