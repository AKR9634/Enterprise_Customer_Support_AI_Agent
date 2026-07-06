from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from psycopg import Connection

from app.repositories.order_repository import OrderRepository


class OrderService:

    @staticmethod
    def get_customer_orders(conn: Connection, customer_id: str) -> list[dict[str, Any]]:
        orders = OrderRepository.list_by_customer(conn, customer_id)
        result: list[dict[str, Any]] = []
        for o in orders:
            items_total = sum(
                Decimal(str(item.quantity)) * item.unit_price
                for item in o.items
            )
            result.append({
                "id": str(o.id),
                "status": o.status,
                "total": str(o.total),
                "items_count": len(o.items),
                "items_total": str(items_total),
                "shipping_address": o.shipping_address,
                "tracking_number": o.tracking_number,
                "created_at": o.created_at.isoformat(),
            })
        return result

    @staticmethod
    def get_order_details(conn: Connection, order_id: str) -> Optional[dict[str, Any]]:
        order = OrderRepository.get_by_id(conn, order_id)
        if order is None:
            return None
        items = [
            {
                "product_id": str(item.product_id),
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "line_total": str(Decimal(str(item.quantity)) * item.unit_price),
            }
            for item in order.items
        ]
        return {
            "id": str(order.id),
            "customer_id": str(order.customer_id),
            "status": order.status,
            "total": str(order.total),
            "shipping_address": order.shipping_address,
            "tracking_number": order.tracking_number,
            "notes": order.notes,
            "items": items,
            "created_at": order.created_at.isoformat(),
        }
