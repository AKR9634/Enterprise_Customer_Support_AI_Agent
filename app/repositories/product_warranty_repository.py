from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from psycopg import Connection


@dataclass
class ProductWarranty:
    id: UUID
    product_id: UUID
    duration_months: int
    terms: str
    created_at: datetime
    updated_at: datetime


_COLUMNS = [
    "id", "product_id", "duration_months", "terms", "created_at", "updated_at",
]


def _row_to_warranty(row: tuple) -> ProductWarranty:
    return ProductWarranty(**dict(zip(_COLUMNS, row)))


class ProductWarrantyRepository:

    @staticmethod
    def get_by_product(conn: Connection, product_id: str) -> Optional[ProductWarranty]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM product_warranties WHERE product_id = %s",
                (product_id,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return _row_to_warranty(row)
