"""
Node 2 — Customer Context. Loads the customer's profile and recent
conversation history via ConversationRepository. No LLM call — a
plain, deterministic data fetch.
"""

from __future__ import annotations

from psycopg import Connection

from app.graph.state import SupportState
from app.repositories.conversation_repository import ConversationRepository

__all__ = [
    "ContextNode",
]


class ContextNode:
    """Graph node that loads conversation history for a given ticket.
    Deterministic — no LLM call involved."""

    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    def __call__(self, state: SupportState) -> dict:
        ticket_id = state.get("ticket_id", "")
        if not ticket_id:
            return {"conversation_history": []}

        messages = ConversationRepository.list_by_ticket(self._conn, ticket_id)
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        return {"conversation_history": history}
