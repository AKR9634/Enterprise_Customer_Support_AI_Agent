from decimal import Decimal
from uuid import uuid4

import pytest
from unittest.mock import MagicMock, patch

from app.repositories.order_repository import Order, OrderItem, OrderRepository


def _mock_order_row(order_id, customer_id, status="pending", total="49.99"):
    return (
        order_id,
        customer_id,
        status,
        total,
        "123 Main St",
        "TRACK123",
        "",
        "2024-01-01 00:00:00+00",
        "2024-01-01 00:00:00+00",
    )


def _mock_item_row(item_id, order_id, product_id, product_name="Widget", quantity=1, unit_price="49.99"):
    return (
        item_id,
        order_id,
        product_id,
        product_name,
        quantity,
        unit_price,
    )


class TestOrderRepository:

    def test_create_returns_order(self):
        oid = uuid4()
        cid = uuid4()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value.fetchone.return_value = _mock_order_row(oid, cid)

        order = OrderRepository.create(mock_conn, str(cid), "49.99")

        assert order.id == oid
        assert order.customer_id == cid
        assert order.status == "pending"
        assert len(order.items) == 0

    def test_get_by_id_found(self):
        oid = uuid4()
        cid = uuid4()
        pid = uuid4()
        iid = uuid4()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = _mock_order_row(oid, cid, "shipped", "139.97")
        mock_cur.fetchall.return_value = [_mock_item_row(iid, oid, pid)]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        order = OrderRepository.get_by_id(mock_conn, str(oid))

        assert order is not None
        assert order.id == oid
        assert order.status == "shipped"
        assert len(order.items) == 1
        assert order.items[0].product_name == "Widget"

    def test_get_by_id_not_found(self):
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value.fetchone.return_value = None

        order = OrderRepository.get_by_id(mock_conn, str(uuid4()))
        assert order is None

    def test_list_by_customer_returns_orders(self):
        cid = uuid4()
        oid1 = uuid4()
        oid2 = uuid4()
        pid = uuid4()
        iid = uuid4()
        mock_cur = MagicMock()
        mock_cur.fetchall.side_effect = [
            [_mock_order_row(oid1, cid, "delivered", "189.97"), _mock_order_row(oid2, cid, "pending", "49.99")],
            [_mock_item_row(iid, oid1, pid)],
        ]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        orders = OrderRepository.list_by_customer(mock_conn, str(cid))

        assert len(orders) == 2
        assert orders[0].status == "delivered"
        assert orders[1].status == "pending"
        assert len(orders[0].items) == 1

    def test_list_by_customer_empty(self):
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        orders = OrderRepository.list_by_customer(mock_conn, str(uuid4()))
        assert orders == []

    def test_update_status_returns_updated(self):
        oid = uuid4()
        cid = uuid4()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = _mock_order_row(oid, cid, "confirmed", "49.99")
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        order = OrderRepository.update_status(mock_conn, str(oid), "confirmed")

        assert order is not None
        assert order.status == "confirmed"

    def test_update_status_not_found(self):
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value.fetchone.return_value = None

        order = OrderRepository.update_status(mock_conn, str(uuid4()), "shipped")
        assert order is None
