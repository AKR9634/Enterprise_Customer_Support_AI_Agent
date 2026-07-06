from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from psycopg import Connection


@dataclass
class OrderItem:
    id: UUID
    order_id: UUID
    product_id: UUID
    product_name: str
    quantity: int
    unit_price: Decimal


@dataclass
class Order:
    id: UUID
    customer_id: UUID
    status: str
    total: Decimal
    shipping_address: str
    tracking_number: str
    notes: str
    created_at: datetime
    updated_at: datetime
    items: list[OrderItem]


_ORDER_COLUMNS = [
    "id", "customer_id", "status", "total", "shipping_address",
    "tracking_number", "notes", "created_at", "updated_at",
]

_ITEM_COLUMNS = [
    "id", "order_id", "product_id", "product_name", "quantity", "unit_price",
]


def _row_to_order(row: tuple) -> Order:
    data = dict(zip(_ORDER_COLUMNS, row))
    data["items"] = []
    return Order(**data)


def _row_to_order_item(row: tuple) -> OrderItem:
    return OrderItem(**dict(zip(_ITEM_COLUMNS, row)))


class OrderRepository:

    @staticmethod
    def create(
        conn: Connection,
        customer_id: str,
        total: str,
        status: str = "pending",
        shipping_address: str = "",
        tracking_number: str = "",
        notes: str = "",
    ) -> Order:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO orders (customer_id, status, total, shipping_address, tracking_number, notes) "
                "VALUES (%s, %s, %s, %s, %s, %s) RETURNING *",
                (customer_id, status, total, shipping_address, tracking_number, notes),
            )
            return _row_to_order(cur.fetchone())

    @staticmethod
    def get_by_id(conn: Connection, order_id: str) -> Optional[Order]:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
            row = cur.fetchone()
            if row is None:
                return None
            order = _row_to_order(row)

            cur.execute(
                "SELECT oi.id, oi.order_id, oi.product_id, p.name, oi.quantity, oi.unit_price "
                "FROM order_items oi "
                "JOIN products p ON p.id = oi.product_id "
                "WHERE oi.order_id = %s "
                "ORDER BY oi.created_at ASC",
                (order_id,),
            )
            order.items = [_row_to_order_item(r) for r in cur.fetchall()]
            return order

    @staticmethod
    def list_by_customer(conn: Connection, customer_id: str) -> list[Order]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM orders WHERE customer_id = %s ORDER BY created_at DESC",
                (customer_id,),
            )
            rows = cur.fetchall()
            orders = [_row_to_order(r) for r in rows]

            if not orders:
                return []

            order_ids = [str(o.id) for o in orders]
            placeholders = ",".join("%s" for _ in order_ids)
            cur.execute(
                f"SELECT oi.id, oi.order_id, oi.product_id, p.name, oi.quantity, oi.unit_price "
                f"FROM order_items oi "
                f"JOIN products p ON p.id = oi.product_id "
                f"WHERE oi.order_id IN ({placeholders}) "
                f"ORDER BY oi.created_at ASC",
                order_ids,
            )
            items_by_order: dict[UUID, list[OrderItem]] = {}
            for r in cur.fetchall():
                item = _row_to_order_item(r)
                items_by_order.setdefault(item.order_id, []).append(item)

            for o in orders:
                o.items = items_by_order.get(o.id, [])

            return orders

    @staticmethod
    def update_status(conn: Connection, order_id: str, new_status: str) -> Optional[Order]:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE orders SET status = %s, updated_at = now() "
                "WHERE id = %s RETURNING *",
                (new_status, order_id),
            )
            row = cur.fetchone()
            if row is None:
                return None
            order = _row_to_order(row)

            cur.execute(
                "SELECT oi.id, oi.order_id, oi.product_id, p.name, oi.quantity, oi.unit_price "
                "FROM order_items oi "
                "JOIN products p ON p.id = oi.product_id "
                "WHERE oi.order_id = %s "
                "ORDER BY oi.created_at ASC",
                (order_id,),
            )
            order.items = [_row_to_order_item(r) for r in cur.fetchall()]
            return order
