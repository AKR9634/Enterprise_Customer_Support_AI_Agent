"""
FastAPI dependency wiring: builds a DB connection, then constructs
each repository and service from it, so routes just declare
Depends(get_ticket_service) instead of wiring this by hand.
"""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from psycopg import Connection

from app.db.session import get_connection


def get_db() -> Generator[Connection, None, None]:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


DbDep = Annotated[Connection, Depends(get_db)]


# ── Service / Repository deps ────────────────────────────────────────────

from app.repositories.conversation_repository import ConversationRepository
from app.services.ticket_service import TicketService


def get_ticket_service() -> TicketService:
    return TicketService()


TicketServiceDep = Annotated[TicketService, Depends(get_ticket_service)]


def get_conversation_repo() -> ConversationRepository:
    return ConversationRepository()


ConversationRepoDep = Annotated[ConversationRepository, Depends(get_conversation_repo)]


from app.repositories.escalation_repository import EscalationRepository


def get_escalation_repo() -> EscalationRepository:
    return EscalationRepository()


EscalationRepoDep = Annotated[EscalationRepository, Depends(get_escalation_repo)]


from app.services.escalation_service import EscalationService


def get_escalation_service() -> EscalationService:
    return EscalationService()


EscalationServiceDep = Annotated[EscalationService, Depends(get_escalation_service)]


# ── LLM deps ──────────────────────────────────────────────────────────────

from app.llm.provider import LLMClient


def get_llm_client() -> LLMClient:
    return LLMClient()


LlmClientDep = Annotated[LLMClient, Depends(get_llm_client)]
