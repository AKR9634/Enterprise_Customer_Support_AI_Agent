"""Unit tests for ContextNode.

Verifies the node loads conversation history via
ConversationRepository.list_by_ticket and only writes
conversation_history. No LLM call is made.
"""

from unittest.mock import MagicMock, patch
from uuid import UUID
from datetime import datetime

import pytest

from app.graph.nodes.context import ContextNode


@pytest.fixture
def mock_conn() -> MagicMock:
    return MagicMock()


def _message(
    role: str,
    content: str,
    msg_id: str = "00000000-0000-0000-0000-000000000001",
    ticket_id: str = "00000000-0000-0000-0000-000000000002",
) -> MagicMock:
    from app.repositories.conversation_repository import ConversationMessage
    return ConversationMessage(
        id=UUID(msg_id),
        ticket_id=UUID(ticket_id),
        role=role,
        content=content,
        created_at=datetime(2025, 6, 1),
    )


class TestContextNode:

    def test_loads_conversation_history(self, mock_conn: MagicMock) -> None:
        with patch(
            "app.graph.nodes.context.ConversationRepository.list_by_ticket",
        ) as mock_list:
            mock_list.return_value = [
                _message("customer", "I need help"),
                _message("agent", "How can I assist?"),
            ]
            node = ContextNode(conn=mock_conn)

            result = node({"ticket_id": "ticket-123"})

        assert result == {
            "conversation_history": [
                {"role": "customer", "content": "I need help"},
                {"role": "agent", "content": "How can I assist?"},
            ]
        }
        mock_list.assert_called_once_with(mock_conn, "ticket-123")

    def test_only_writes_own_field(self, mock_conn: MagicMock) -> None:
        with patch(
            "app.graph.nodes.context.ConversationRepository.list_by_ticket",
            return_value=[],
        ):
            node = ContextNode(conn=mock_conn)

            result = node({
                "ticket_id": "t-1",
                "customer_message": "hello",
                "category": "general",
            })

        assert set(result.keys()) == {"conversation_history"}

    def test_no_ticket_id_returns_empty_history(self, mock_conn: MagicMock) -> None:
        node = ContextNode(conn=mock_conn)

        result = node({})

        assert result == {"conversation_history": []}

    def test_empty_ticket_id_returns_empty_history(self, mock_conn: MagicMock) -> None:
        node = ContextNode(conn=mock_conn)

        result = node({"ticket_id": ""})

        assert result == {"conversation_history": []}

    def test_does_not_call_llm(self, mock_conn: MagicMock) -> None:
        with patch(
            "app.graph.nodes.context.ConversationRepository.list_by_ticket",
            return_value=[],
        ):
            node = ContextNode(conn=mock_conn)

            result = node({"ticket_id": "t-1"})

        assert result == {"conversation_history": []}
