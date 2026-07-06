from decimal import Decimal
from uuid import uuid4

import pytest
from unittest.mock import MagicMock, patch

from app.repositories.product_repository import Product, ProductRepository


def _mock_row(product_id, name="Widget", price=Decimal("49.99"), sku="WIDGET-001"):
    return (
        product_id,
        name,
        "A widget",
        price,
        sku,
        "2024-01-01 00:00:00+00",
        "2024-01-01 00:00:00+00",
    )


class TestProductRepository:

    def test_list_all_returns_products(self):
        pid = uuid4()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = [
            _mock_row(pid),
        ]

        products = ProductRepository.list_all(mock_conn)

        assert len(products) == 1
        assert products[0].id == pid
        assert products[0].name == "Widget"
        assert products[0].price == Decimal("49.99")

    def test_list_all_empty(self):
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = []

        products = ProductRepository.list_all(mock_conn)
        assert products == []

    def test_get_by_id_found(self):
        pid = uuid4()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value.fetchone.return_value = _mock_row(pid)

        product = ProductRepository.get_by_id(mock_conn, str(pid))

        assert product is not None
        assert product.id == pid
        assert product.sku == "WIDGET-001"

    def test_get_by_id_not_found(self):
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value.fetchone.return_value = None

        product = ProductRepository.get_by_id(mock_conn, str(uuid4()))
        assert product is None
