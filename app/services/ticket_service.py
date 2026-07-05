"""
Business rules for tickets: create_ticket, transition_status
(enforces the open -> pending -> resolved/escalated -> closed state
machine), and set_priority. The only place ticket rules are allowed
to live.
"""

from __future__ import annotations

from typing import Optional

from psycopg import Connection

from app.repositories.ticket_repository import Ticket, TicketRepository

__all__ = [
    "InvalidTicketTransition",
    "TicketService",
]


class InvalidTicketTransition(Exception):
    """Raised when an illegal ticket status transition is attempted."""

    def __init__(self, ticket_id: str, current_status: str, new_status: str) -> None:
        self.ticket_id = ticket_id
        self.current_status = current_status
        self.new_status = new_status
        super().__init__(
            f"Cannot transition ticket {ticket_id} from {current_status} to {new_status}"
        )


_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "open": {"pending"},
    "pending": {"resolved", "escalated"},
    "resolved": {"closed"},
    "escalated": {"closed"},
    "closed": set(),
}


class TicketService:

    @staticmethod
    def create_ticket(
        conn: Connection,
        customer_id: str,
        subject: str,
        priority: str = "normal",
    ) -> Ticket:
        return TicketRepository.create(conn, customer_id, subject, priority)

    @staticmethod
    def get_ticket(conn: Connection, ticket_id: str) -> Optional[Ticket]:
        return TicketRepository.get_by_id(conn, ticket_id)

    @staticmethod
    def list_tickets(conn: Connection, current_user: dict) -> list[Ticket]:
        if current_user["role"] == "agent":
            return TicketRepository.list_all(conn)
        return TicketRepository.list_by_customer(conn, str(current_user["id"]))

    @staticmethod
    def transition_status(
        conn: Connection,
        ticket_id: str,
        new_status: str,
    ) -> Ticket:
        ticket = TicketRepository.get_by_id(conn, ticket_id)
        if ticket is None:
            raise ValueError(f"Ticket {ticket_id} not found")

        allowed = _ALLOWED_TRANSITIONS.get(ticket.status, set())
        if new_status not in allowed:
            raise InvalidTicketTransition(ticket_id, ticket.status, new_status)

        result = TicketRepository.update_status(conn, ticket_id, new_status)
        assert result is not None, f"Ticket {ticket_id} deleted between get and update"
        return result
