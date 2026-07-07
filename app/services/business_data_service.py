from __future__ import annotations

from typing import Any

from psycopg import Connection

from app.services.account_service import AccountService
from app.services.billing_service import BillingService
from app.services.order_service import OrderService
from app.services.product_service import ProductService


class BusinessDataService:

    @staticmethod
    def get_business_data(
        conn: Connection,
        customer_id: str,
        category: str,
        query_text: str = "",
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}

        if category == "order":
            result["orders"] = OrderService.get_customer_orders(conn, customer_id)

        elif category == "billing":
            result["subscriptions"] = BillingService.get_customer_subscriptions(
                conn, customer_id
            )
            result["invoices"] = BillingService.get_customer_invoices(conn, customer_id)

        elif category == "account":
            result["profile"] = AccountService.get_customer_profile(conn, customer_id)
            result["addresses"] = AccountService.get_customer_addresses(conn, customer_id)
            result["account_metadata"] = AccountService.get_account_metadata(conn, customer_id)

        elif category == "product":
            result["products"] = ProductService.search_products(conn, query_text)
            if result["products"]:
                pid = result["products"][0]["id"]
                result["specifications"] = ProductService.get_product_specs(conn, pid)
                result["warranty"] = ProductService.get_product_warranty(conn, pid)
                result["inventory"] = ProductService.get_inventory_status(conn, pid)

        return result
