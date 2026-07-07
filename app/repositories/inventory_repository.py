from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from psycopg import Connection


@dataclass
class Inventory:
    id: UUID
    product_id: UUID
    stock_count: int
    low_stock: int
    updated_at: datetime


_COLUMNS = [
    "id", "product_id", "stock_count", "low_stock", "updated_at",
]


def _row_to_inventory(row: tuple) -> Inventory:
    return Inventory(**dict(zip(_COLUMNS, row)))


class InventoryRepository:

    @staticmethod
    def get_by_product(conn: Connection, product_id: str) -> Optional[Inventory]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM inventory WHERE product_id = %s",
                (product_id,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return _row_to_inventory(row)
