from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from psycopg import Connection


@dataclass
class Ticket:
    id: UUID
    customer_id: UUID
    subject: str
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime


_COLUMNS = ["id", "customer_id", "subject", "status", "priority", "created_at", "updated_at"]


def _row_to_ticket(row: tuple) -> Ticket:
    return Ticket(**dict(zip(_COLUMNS, row)))


class TicketRepository:

    @staticmethod
    def create(
        conn: Connection,
        customer_id: str,
        subject: str,
        priority: str = "normal",
    ) -> Ticket:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO tickets (customer_id, subject, status, priority) "
                "VALUES (%s, %s, %s, %s) RETURNING *",
                (customer_id, subject, "open", priority),
            )
            return _row_to_ticket(cur.fetchone())

    @staticmethod
    def get_by_id(conn: Connection, ticket_id: str) -> Optional[Ticket]:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM tickets WHERE id = %s", (ticket_id,))
            row = cur.fetchone()
            if row is None:
                return None
            return _row_to_ticket(row)

    @staticmethod
    def list_by_customer(conn: Connection, customer_id: str) -> list[Ticket]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM tickets WHERE customer_id = %s ORDER BY created_at DESC",
                (customer_id,),
            )
            return [_row_to_ticket(row) for row in cur.fetchall()]

    @staticmethod
    def update_status(conn: Connection, ticket_id: str, new_status: str) -> Optional[Ticket]:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE tickets SET status = %s, updated_at = now() "
                "WHERE id = %s RETURNING *",
                (new_status, ticket_id),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return _row_to_ticket(row)
