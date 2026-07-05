from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from psycopg import Connection


@dataclass
class ConversationMessage:
    id: UUID
    ticket_id: UUID
    role: str
    content: str
    created_at: datetime


_COLUMNS = ["id", "ticket_id", "role", "content", "created_at"]


def _row_to_message(row: tuple) -> ConversationMessage:
    return ConversationMessage(**dict(zip(_COLUMNS, row)))


class ConversationRepository:

    @staticmethod
    def append_message(
        conn: Connection,
        ticket_id: str,
        role: str,
        content: str,
    ) -> ConversationMessage:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO conversations (ticket_id, role, content) "
                "VALUES (%s, %s, %s) RETURNING *",
                (ticket_id, role, content),
            )
            return _row_to_message(cur.fetchone())

    @staticmethod
    def list_by_ticket(conn: Connection, ticket_id: str) -> list[ConversationMessage]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM conversations WHERE ticket_id = %s ORDER BY created_at ASC",
                (ticket_id,),
            )
            return [_row_to_message(row) for row in cur.fetchall()]
