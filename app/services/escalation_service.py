"""
evaluate() decides whether a chat turn should escalate (confidence
or grounding failure); enqueue(), claim(), and resolve() manage an
escalation through its lifecycle in the human review queue.
"""

from __future__ import annotations

from typing import Any, Optional

import structlog
from psycopg import Connection

from app import config
from app.repositories.escalation_repository import EscalationRepository
from app.services.ticket_service import TicketService

logger = structlog.get_logger(__name__)

__all__ = [
    "EscalationConflictError",
    "EscalationService",
]


class EscalationConflictError(Exception):
    """Raised when an escalation cannot be claimed because it is
    already claimed or not found."""

    def __init__(self, escalation_id: str, agent_id: str) -> None:
        self.escalation_id = escalation_id
        self.agent_id = agent_id
        super().__init__(
            f"Escalation {escalation_id} already claimed or not found "
            f"(agent {agent_id})"
        )


class EscalationService:
    """Deterministic escalation evaluation and lifecycle management."""

    @staticmethod
    def evaluate(
        confidence: float | None,
        *,
        threshold: float | None = None,
    ) -> tuple[bool, str | None]:
        """Return (escalate, reason) based on confidence vs threshold.

        A confidence of *None* or below the threshold triggers escalation.
        """
        threshold = threshold if threshold is not None else config.CONFIDENCE_THRESHOLD

        if confidence is None:
            return True, "No confidence score available"

        if confidence < threshold:
            return True, (
                f"Confidence {confidence:.2f} is below threshold {threshold:.2f}"
            )

        return False, None

    # ── Lifecycle (Phase 5) ────────────────────────────────────────────────

    def enqueue(
        self,
        conn: Connection,
        ticket_id: str,
        escalation_reason: str,
        category: Optional[str] = None,
        confidence: Optional[float] = None,
        customer_message: Optional[str] = None,
        draft_response: Optional[str] = None,
        routing_reason: Optional[str] = None,
        retrieved_docs: Optional[list[dict[str, Any]]] = None,
        business_data: Optional[dict[str, Any]] = None,
        priority: str = "normal",
    ) -> Any:
        """Persist an escalation record and transition the ticket to escalated."""
        escalation = EscalationRepository.create(
            conn,
            ticket_id=ticket_id,
            escalation_reason=escalation_reason,
            category=category,
            confidence=confidence,
            customer_message=customer_message,
            draft_response=draft_response,
            routing_reason=routing_reason,
            retrieved_docs=retrieved_docs,
            business_data=business_data,
            priority=priority,
        )

        TicketService.transition_status(conn, ticket_id, "escalated")

        logger.info("escalation_enqueued", escalation_id=str(escalation.id), ticket_id=ticket_id)
        return escalation

    def claim(self, conn: Connection, escalation_id: str, agent_id: str) -> Any:
        """Atomically claim an escalation; raises EscalationConflictError if not available."""
        escalation = EscalationRepository.claim_atomic(conn, escalation_id, agent_id)
        if escalation is None:
            logger.warning(
                "escalation_claim_conflict",
                escalation_id=escalation_id,
                agent_id=agent_id,
            )
            raise EscalationConflictError(escalation_id, agent_id)

        TicketService.transition_status(conn, str(escalation.ticket_id), "pending")

        logger.info(
            "escalation_claimed",
            escalation_id=escalation_id,
            agent_id=agent_id,
            ticket_id=str(escalation.ticket_id),
        )
        return escalation

    def resolve(self, conn: Connection, escalation_id: str) -> Any:
        """Mark an escalation as resolved and transition the parent ticket."""
        escalation = EscalationRepository.update_status(conn, escalation_id, "resolved")
        if escalation is None:
            raise ValueError(f"Escalation {escalation_id} not found")

        TicketService.transition_status(conn, str(escalation.ticket_id), "resolved")

        logger.info(
            "escalation_resolved",
            escalation_id=escalation_id,
            ticket_id=str(escalation.ticket_id),
        )
        return escalation
