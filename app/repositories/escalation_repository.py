import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from psycopg import Connection


@dataclass
class Escalation:
    id: UUID
    ticket_id: UUID
    status: str
    priority: str
    assigned_reviewer: Optional[UUID]
    escalation_reason: str
    category: Optional[str]
    confidence: Optional[float]
    customer_message: Optional[str]
    draft_response: Optional[str]
    routing_reason: Optional[str]
    retrieved_docs: list[dict[str, Any]]
    business_data: dict[str, Any]
    created_at: datetime
    updated_at: datetime


_COLUMNS = [
    "id", "ticket_id", "status", "priority", "assigned_reviewer",
    "escalation_reason", "category", "confidence",
    "customer_message", "draft_response", "routing_reason",
    "retrieved_docs", "business_data", "created_at", "updated_at",
]


def _row_to_escalation(row: tuple) -> Escalation:
    data = dict(zip(_COLUMNS, row))
    if data["retrieved_docs"] is None:
        data["retrieved_docs"] = []
    if data["business_data"] is None:
        data["business_data"] = {}
    return Escalation(**data)


class EscalationRepository:

    @staticmethod
    def create(
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
    ) -> Escalation:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO escalations "
                "(ticket_id, escalation_reason, category, confidence, "
                " customer_message, draft_response, routing_reason, "
                " retrieved_docs, business_data, priority) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING *",
                (
                    ticket_id, escalation_reason, category, confidence,
                    customer_message, draft_response, routing_reason,
                    json.dumps(retrieved_docs or []),
                    json.dumps(business_data or {}),
                    priority,
                ),
            )
            return _row_to_escalation(cur.fetchone())

    @staticmethod
    def get_by_id(conn: Connection, escalation_id: str) -> Optional[Escalation]:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM escalations WHERE id = %s", (escalation_id,))
            row = cur.fetchone()
            if row is None:
                return None
            return _row_to_escalation(row)

    @staticmethod
    def list_queued(conn: Connection) -> list[Escalation]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM escalations WHERE status = 'queued' "
                "ORDER BY "
                "  CASE priority "
                "    WHEN 'urgent' THEN 0 "
                "    WHEN 'high' THEN 1 "
                "    WHEN 'normal' THEN 2 "
                "    WHEN 'low' THEN 3 "
                "  END, "
                "created_at ASC",
            )
            return [_row_to_escalation(row) for row in cur.fetchall()]

    @staticmethod
    def update_status(conn: Connection, escalation_id: str, new_status: str) -> Optional[Escalation]:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE escalations SET status = %s, updated_at = now() "
                "WHERE id = %s RETURNING *",
                (new_status, escalation_id),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return _row_to_escalation(row)

    @staticmethod
    def assign_reviewer(conn: Connection, escalation_id: str, reviewer_id: str) -> Optional[Escalation]:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE escalations SET assigned_reviewer = %s, updated_at = now() "
                "WHERE id = %s RETURNING *",
                (reviewer_id, escalation_id),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return _row_to_escalation(row)

    @staticmethod
    def list_resolved(conn: Connection, reviewer_id: str) -> list[Escalation]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM escalations "
                "WHERE assigned_reviewer = %s AND status = 'resolved' "
                "ORDER BY updated_at DESC",
                (reviewer_id,),
            )
            return [_row_to_escalation(row) for row in cur.fetchall()]

    @staticmethod
    def claim_atomic(conn: Connection, escalation_id: str, reviewer_id: str) -> Optional[Escalation]:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE escalations "
                "SET status = 'in_review', assigned_reviewer = %s, updated_at = now() "
                "WHERE id = %s AND status = 'queued' AND assigned_reviewer IS NULL "
                "RETURNING *",
                (reviewer_id, escalation_id),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return _row_to_escalation(row)
