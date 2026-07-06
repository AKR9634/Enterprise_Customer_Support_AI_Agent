from decimal import Decimal
from uuid import uuid4

import pytest
from unittest.mock import MagicMock, patch

from app.repositories.subscription_repository import Subscription, SubscriptionRepository


def _mock_row(sub_id, customer_id, plan_name="Pro Monthly", status="active", price=Decimal("29.99")):
    return (
        sub_id,
        customer_id,
        plan_name,
        status,
        Decimal(price) if not isinstance(price, Decimal) else price,
        "2024-01-01 00:00:00+00",
        "2024-06-01 00:00:00+00",
        None,
        "2024-01-01 00:00:00+00",
        "2024-01-01 00:00:00+00",
    )


class TestSubscriptionRepository:

    def test_list_by_customer_returns_subscriptions(self):
        sid = uuid4()
        cid = uuid4()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = [
            _mock_row(sid, cid),
        ]

        subs = SubscriptionRepository.list_by_customer(mock_conn, str(cid))

        assert len(subs) == 1
        assert subs[0].id == sid
        assert subs[0].plan_name == "Pro Monthly"
        assert subs[0].status == "active"
        assert subs[0].price == Decimal("29.99")

    def test_list_by_customer_empty(self):
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = []

        subs = SubscriptionRepository.list_by_customer(mock_conn, str(uuid4()))
        assert subs == []

    def test_get_by_id_found(self):
        sid = uuid4()
        cid = uuid4()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value.fetchone.return_value = _mock_row(sid, cid)

        sub = SubscriptionRepository.get_by_id(mock_conn, str(sid))

        assert sub is not None
        assert sub.id == sid
        assert sub.plan_name == "Pro Monthly"

    def test_get_by_id_not_found(self):
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value.fetchone.return_value = None

        sub = SubscriptionRepository.get_by_id(mock_conn, str(uuid4()))
        assert sub is None
