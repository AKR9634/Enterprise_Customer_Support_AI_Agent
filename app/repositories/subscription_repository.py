from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from psycopg import Connection


@dataclass
class Subscription:
    id: UUID
    customer_id: UUID
    plan_name: str
    status: str
    price: Decimal
    started_at: datetime
    next_billing: Optional[datetime]
    cancelled_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


_COLUMNS = [
    "id", "customer_id", "plan_name", "status", "price",
    "started_at", "next_billing", "cancelled_at", "created_at", "updated_at",
]


def _row_to_subscription(row: tuple) -> Subscription:
    return Subscription(**dict(zip(_COLUMNS, row)))


class SubscriptionRepository:

    @staticmethod
    def list_by_customer(conn: Connection, customer_id: str) -> list[Subscription]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM subscriptions WHERE customer_id = %s ORDER BY created_at DESC",
                (customer_id,),
            )
            return [_row_to_subscription(row) for row in cur.fetchall()]

    @staticmethod
    def get_by_id(conn: Connection, subscription_id: str) -> Optional[Subscription]:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM subscriptions WHERE id = %s", (subscription_id,))
            row = cur.fetchone()
            if row is None:
                return None
            return _row_to_subscription(row)
