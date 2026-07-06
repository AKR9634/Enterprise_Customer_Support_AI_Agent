from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from unittest.mock import MagicMock, patch

from app.repositories.order_repository import Order, OrderItem
from app.services.order_service import OrderService


def _make_order(
    order_id=None,
    customer_id=None,
    status="delivered",
    total="189.97",
    items=None,
):
    oid = order_id or uuid4()
    cid = customer_id or uuid4()
    order = Order(
        id=oid,
        customer_id=cid,
        status=status,
        total=Decimal(total),
        shipping_address="123 Main St",
        tracking_number="TRACK123",
        notes="",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        items=items or [],
    )
    return order


def _make_item(product_name="Widget", quantity=2, unit_price="49.99"):
    return OrderItem(
        id=uuid4(),
        order_id=uuid4(),
        product_id=uuid4(),
        product_name=product_name,
        quantity=quantity,
        unit_price=Decimal(unit_price),
    )


class TestOrderService:

    def test_get_customer_orders_returns_summaries(self):
        cid = uuid4()
        items = [_make_item("Widget Pro", 2, "49.99"), _make_item("Gadget X", 1, "89.99")]
        orders = [
            _make_order(customer_id=cid, status="delivered", total="189.97", items=items),
            _make_order(customer_id=cid, status="pending", total="49.99", items=[_make_item("Widget Pro", 1, "49.99")]),
        ]

        with patch("app.services.order_service.OrderRepository.list_by_customer", return_value=orders) as mock_list:
            result = OrderService.get_customer_orders(MagicMock(), str(cid))

        mock_list.assert_called_once()
        assert len(result) == 2
        assert result[0]["status"] == "delivered"
        assert result[0]["items_count"] == 2
        assert result[1]["status"] == "pending"
        assert result[1]["items_count"] == 1

    def test_get_customer_orders_empty(self):
        cid = uuid4()
        with patch("app.services.order_service.OrderRepository.list_by_customer", return_value=[]):
            result = OrderService.get_customer_orders(MagicMock(), str(cid))

        assert result == []

    def test_get_order_details_returns_full(self):
        oid = uuid4()
        items = [_make_item("Widget Pro", 2, "49.99")]
        order = _make_order(order_id=oid, items=items)

        with patch("app.services.order_service.OrderRepository.get_by_id", return_value=order) as mock_get:
            result = OrderService.get_order_details(MagicMock(), str(oid))

        mock_get.assert_called_once()
        assert result is not None
        assert result["id"] == str(oid)
        assert len(result["items"]) == 1
        assert result["items"][0]["product_name"] == "Widget Pro"
        assert result["items"][0]["line_total"] == "99.98"

    def test_get_order_details_not_found(self):
        with patch("app.services.order_service.OrderRepository.get_by_id", return_value=None):
            result = OrderService.get_order_details(MagicMock(), str(uuid4()))

        assert result is None
