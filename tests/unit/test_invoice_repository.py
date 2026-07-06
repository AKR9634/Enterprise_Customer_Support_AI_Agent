from decimal import Decimal
from uuid import uuid4

import pytest
from unittest.mock import MagicMock, patch

from app.repositories.invoice_repository import Invoice, InvoiceRepository


def _mock_row(inv_id, customer_id, amount=Decimal("29.99"), status="paid"):
    return (
        inv_id,
        customer_id,
        None,
        None,
        Decimal(amount) if not isinstance(amount, Decimal) else amount,
        status,
        "2024-06-01 00:00:00+00",
        "2024-05-15 00:00:00+00",
        "2024-01-01 00:00:00+00",
        "2024-01-01 00:00:00+00",
    )


class TestInvoiceRepository:

    def test_list_by_customer_returns_invoices(self):
        iid = uuid4()
        cid = uuid4()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = [
            _mock_row(iid, cid),
        ]

        invoices = InvoiceRepository.list_by_customer(mock_conn, str(cid))

        assert len(invoices) == 1
        assert invoices[0].id == iid
        assert invoices[0].amount == Decimal("29.99")
        assert invoices[0].status == "paid"

    def test_list_by_customer_empty(self):
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = []

        invoices = InvoiceRepository.list_by_customer(mock_conn, str(uuid4()))
        assert invoices == []

    def test_list_by_subscription_returns_invoices(self):
        sid = uuid4()
        inv_id = uuid4()
        cid = uuid4()

        mock_row = (
            inv_id,
            cid,
            sid,
            None,
            "29.99",
            "paid",
            "2024-06-01 00:00:00+00",
            "2024-05-15 00:00:00+00",
            "2024-01-01 00:00:00+00",
            "2024-01-01 00:00:00+00",
        )

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = [mock_row]

        invoices = InvoiceRepository.list_by_subscription(mock_conn, str(sid))

        assert len(invoices) == 1
        assert invoices[0].subscription_id == sid
