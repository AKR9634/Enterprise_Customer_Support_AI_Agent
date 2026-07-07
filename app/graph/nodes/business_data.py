from __future__ import annotations

from typing import Any

from psycopg import Connection

from app.graph.state import SupportState
from app.services.business_data_service import BusinessDataService

__all__ = [
    "BusinessDataNode",
]

DATA_CATEGORIES = {"billing", "order"}


class BusinessDataNode:
    """Graph node that fetches customer business data (orders,
    subscriptions, invoices) when the category requires it.

    Deterministic — no LLM call involved. Skips all DB lookups for
    categories that do not need business data (e.g. ``general``).
    """

    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    def __call__(self, state: SupportState) -> dict[str, Any]:
        customer_id = state.get("customer_id")
        category = state.get("category")

        if not customer_id or not category or category not in DATA_CATEGORIES:
            return {"business_data": {}}

        data = BusinessDataService.get_business_data(
            conn=self._conn,
            customer_id=customer_id,
            category=category,
        )
        return {"business_data": data}
