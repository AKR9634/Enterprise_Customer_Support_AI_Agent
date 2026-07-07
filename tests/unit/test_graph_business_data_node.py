"""Unit tests for BusinessDataNode.

Verifies the node conditionally calls BusinessDataService based on
category and only writes the business_data field.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.graph.nodes.business_data import BusinessDataNode


@pytest.fixture
def mock_conn() -> MagicMock:
    return MagicMock()


class TestBusinessDataNode:

    def test_billing_category_calls_service(self, mock_conn: MagicMock) -> None:
        with patch(
            "app.graph.nodes.business_data.BusinessDataService.get_business_data",
        ) as mock_svc:
            mock_svc.return_value = {
                "subscriptions": [{"id": "sub-1", "plan_name": "Pro", "status": "active"}],
                "invoices": [{"id": "inv-1", "amount": "29.99", "status": "paid"}],
            }
            node = BusinessDataNode(conn=mock_conn)

            result = node({
                "customer_id": "cust-123",
                "category": "billing",
            })

        assert result["business_data"] == {
            "subscriptions": [{"id": "sub-1", "plan_name": "Pro", "status": "active"}],
            "invoices": [{"id": "inv-1", "amount": "29.99", "status": "paid"}],
        }
        mock_svc.assert_called_once_with(
            conn=mock_conn,
            customer_id="cust-123",
            category="billing",
        )

    def test_order_category_calls_service(self, mock_conn: MagicMock) -> None:
        with patch(
            "app.graph.nodes.business_data.BusinessDataService.get_business_data",
        ) as mock_svc:
            mock_svc.return_value = {
                "orders": [{"id": "ord-1", "status": "shipped", "total": "49.99"}],
            }
            node = BusinessDataNode(conn=mock_conn)

            result = node({
                "customer_id": "cust-456",
                "category": "order",
            })

        assert "orders" in result["business_data"]
        mock_svc.assert_called_once_with(
            conn=mock_conn,
            customer_id="cust-456",
            category="order",
        )

    def test_general_category_skips_db(self, mock_conn: MagicMock) -> None:
        with patch(
            "app.graph.nodes.business_data.BusinessDataService.get_business_data",
        ) as mock_svc:
            node = BusinessDataNode(conn=mock_conn)

            result = node({
                "customer_id": "cust-789",
                "category": "general",
            })

        assert result == {"business_data": {}}
        mock_svc.assert_not_called()

    def test_unknown_category_skips_db(self, mock_conn: MagicMock) -> None:
        with patch(
            "app.graph.nodes.business_data.BusinessDataService.get_business_data",
        ) as mock_svc:
            node = BusinessDataNode(conn=mock_conn)

            result = node({
                "customer_id": "cust-999",
                "category": None,
            })

        assert result == {"business_data": {}}
        mock_svc.assert_not_called()

    def test_no_customer_id_skips_db(self, mock_conn: MagicMock) -> None:
        with patch(
            "app.graph.nodes.business_data.BusinessDataService.get_business_data",
        ) as mock_svc:
            node = BusinessDataNode(conn=mock_conn)

            result = node({
                "category": "billing",
            })

        assert result == {"business_data": {}}
        mock_svc.assert_not_called()

    def test_only_writes_own_field(self, mock_conn: MagicMock) -> None:
        with patch(
            "app.graph.nodes.business_data.BusinessDataService.get_business_data",
            return_value={"orders": []},
        ):
            node = BusinessDataNode(conn=mock_conn)

            result = node({
                "customer_id": "cust-1",
                "category": "order",
                "ticket_id": "t-1",
                "customer_message": "hello",
            })

        assert set(result.keys()) == {"business_data"}
