from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from psycopg import Connection


@dataclass
class ProductSpecification:
    id: UUID
    product_id: UUID
    key: str
    value: str
    created_at: datetime


_COLUMNS = [
    "id", "product_id", "key", "value", "created_at",
]


def _row_to_spec(row: tuple) -> ProductSpecification:
    return ProductSpecification(**dict(zip(_COLUMNS, row)))


class ProductSpecificationRepository:

    @staticmethod
    def list_by_product(conn: Connection, product_id: str) -> list[ProductSpecification]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM product_specifications WHERE product_id = %s ORDER BY key ASC",
                (product_id,),
            )
            return [_row_to_spec(row) for row in cur.fetchall()]
