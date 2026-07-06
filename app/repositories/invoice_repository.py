from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from psycopg import Connection


@dataclass
class Invoice:
    id: UUID
    customer_id: UUID
    subscription_id: Optional[UUID]
    order_id: Optional[UUID]
    amount: Decimal
    status: str
    due_date: datetime
    paid_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


_COLUMNS = [
    "id", "customer_id", "subscription_id", "order_id", "amount",
    "status", "due_date", "paid_at", "created_at", "updated_at",
]


def _row_to_invoice(row: tuple) -> Invoice:
    return Invoice(**dict(zip(_COLUMNS, row)))


class InvoiceRepository:

    @staticmethod
    def list_by_customer(conn: Connection, customer_id: str) -> list[Invoice]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM invoices WHERE customer_id = %s ORDER BY due_date DESC",
                (customer_id,),
            )
            return [_row_to_invoice(row) for row in cur.fetchall()]

    @staticmethod
    def list_by_subscription(conn: Connection, subscription_id: str) -> list[Invoice]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM invoices WHERE subscription_id = %s ORDER BY due_date DESC",
                (subscription_id,),
            )
            return [_row_to_invoice(row) for row in cur.fetchall()]
