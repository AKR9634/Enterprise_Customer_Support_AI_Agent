from __future__ import annotations

from typing import Any

from psycopg import Connection

from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.invoice_repository import InvoiceRepository


class BillingService:

    @staticmethod
    def get_customer_subscriptions(conn: Connection, customer_id: str) -> list[dict[str, Any]]:
        subs = SubscriptionRepository.list_by_customer(conn, customer_id)
        return [
            {
                "id": str(s.id),
                "plan_name": s.plan_name,
                "status": s.status,
                "price": str(s.price),
                "started_at": s.started_at.isoformat(),
                "next_billing": s.next_billing.isoformat() if s.next_billing else None,
                "cancelled_at": s.cancelled_at.isoformat() if s.cancelled_at else None,
            }
            for s in subs
        ]

    @staticmethod
    def get_customer_invoices(conn: Connection, customer_id: str) -> list[dict[str, Any]]:
        invoices = InvoiceRepository.list_by_customer(conn, customer_id)
        return [
            {
                "id": str(inv.id),
                "amount": str(inv.amount),
                "status": inv.status,
                "due_date": inv.due_date.isoformat(),
                "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
            }
            for inv in invoices
        ]
