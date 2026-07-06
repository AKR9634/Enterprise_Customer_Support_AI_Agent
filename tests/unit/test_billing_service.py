from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from unittest.mock import MagicMock, patch

from app.repositories.subscription_repository import Subscription
from app.repositories.invoice_repository import Invoice
from app.services.billing_service import BillingService


def _make_subscription(customer_id=None, plan_name="Pro Monthly", status="active", price="29.99"):
    return Subscription(
        id=uuid4(),
        customer_id=customer_id or uuid4(),
        plan_name=plan_name,
        status=status,
        price=Decimal(price),
        started_at=datetime.now(timezone.utc),
        next_billing=datetime.now(timezone.utc),
        cancelled_at=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def _make_invoice(customer_id=None, amount="29.99", status="paid"):
    return Invoice(
        id=uuid4(),
        customer_id=customer_id or uuid4(),
        subscription_id=None,
        order_id=None,
        amount=Decimal(amount),
        status=status,
        due_date=datetime.now(timezone.utc),
        paid_at=datetime.now(timezone.utc) if status == "paid" else None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class TestBillingService:

    def test_get_customer_subscriptions_returns_active(self):
        cid = uuid4()
        subs = [
            _make_subscription(customer_id=cid, plan_name="Pro Monthly", price="29.99"),
            _make_subscription(customer_id=cid, plan_name="Add-on Pack", price="9.99"),
        ]

        with patch("app.services.billing_service.SubscriptionRepository.list_by_customer", return_value=subs) as mock_list:
            result = BillingService.get_customer_subscriptions(MagicMock(), str(cid))

        mock_list.assert_called_once()
        assert len(result) == 2
        assert result[0]["plan_name"] == "Pro Monthly"
        assert result[0]["price"] == "29.99"
        assert result[1]["plan_name"] == "Add-on Pack"

    def test_get_customer_subscriptions_empty(self):
        cid = uuid4()
        with patch("app.services.billing_service.SubscriptionRepository.list_by_customer", return_value=[]):
            result = BillingService.get_customer_subscriptions(MagicMock(), str(cid))

        assert result == []

    def test_get_customer_invoices_returns_history(self):
        cid = uuid4()
        invoices = [
            _make_invoice(customer_id=cid, amount="29.99", status="paid"),
            _make_invoice(customer_id=cid, amount="29.99", status="pending"),
        ]

        with patch("app.services.billing_service.InvoiceRepository.list_by_customer", return_value=invoices) as mock_list:
            result = BillingService.get_customer_invoices(MagicMock(), str(cid))

        mock_list.assert_called_once()
        assert len(result) == 2
        assert result[0]["status"] == "paid"
        assert result[0]["amount"] == "29.99"
        assert result[1]["status"] == "pending"
        assert result[1]["paid_at"] is None

    def test_get_customer_invoices_empty(self):
        cid = uuid4()
        with patch("app.services.billing_service.InvoiceRepository.list_by_customer", return_value=[]):
            result = BillingService.get_customer_invoices(MagicMock(), str(cid))

        assert result == []
