from __future__ import annotations

from typing import Any

from psycopg import Connection

from app.services.billing_service import BillingService
from app.services.order_service import OrderService


class BusinessDataService:

    @staticmethod
    def get_business_data(
        conn: Connection,
        customer_id: str,
        category: str,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}

        if category == "order":
            result["orders"] = OrderService.get_customer_orders(conn, customer_id)

        elif category == "billing":
            result["subscriptions"] = BillingService.get_customer_subscriptions(
                conn, customer_id
            )
            result["invoices"] = BillingService.get_customer_invoices(conn, customer_id)

        return result
