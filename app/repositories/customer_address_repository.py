from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from psycopg import Connection


@dataclass
class CustomerAddress:
    id: UUID
    customer_id: UUID
    label: str
    street: str
    city: str
    state: str
    zip: str
    country: str
    is_default: bool
    created_at: datetime
    updated_at: datetime


_COLUMNS = [
    "id", "customer_id", "label", "street", "city", "state",
    "zip", "country", "is_default", "created_at", "updated_at",
]


def _row_to_address(row: tuple) -> CustomerAddress:
    return CustomerAddress(**dict(zip(_COLUMNS, row)))


class CustomerAddressRepository:

    @staticmethod
    def list_by_customer(conn: Connection, customer_id: str) -> list[CustomerAddress]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM customer_addresses WHERE customer_id = %s ORDER BY is_default DESC, label ASC",
                (customer_id,),
            )
            return [_row_to_address(row) for row in cur.fetchall()]

    @staticmethod
    def get_default(conn: Connection, customer_id: str) -> Optional[CustomerAddress]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM customer_addresses WHERE customer_id = %s AND is_default = true LIMIT 1",
                (customer_id,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return _row_to_address(row)
