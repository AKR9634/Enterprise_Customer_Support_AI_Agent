from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from psycopg import Connection


@dataclass
class Product:
    id: UUID
    name: str
    description: str
    price: Decimal
    sku: str
    created_at: datetime
    updated_at: datetime


_COLUMNS = ["id", "name", "description", "price", "sku", "created_at", "updated_at"]


def _row_to_product(row: tuple) -> Product:
    return Product(**dict(zip(_COLUMNS, row)))


class ProductRepository:

    @staticmethod
    def list_all(conn: Connection) -> list[Product]:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM products ORDER BY name ASC")
            return [_row_to_product(row) for row in cur.fetchall()]

    @staticmethod
    def get_by_id(conn: Connection, product_id: str) -> Optional[Product]:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            row = cur.fetchone()
            if row is None:
                return None
            return _row_to_product(row)
