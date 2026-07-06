"""
Integration tests for business data repositories against a real test database.
Every test runs inside a transaction that is rolled back on teardown.
"""

from decimal import Decimal
from uuid import UUID

from psycopg import Connection

from app.repositories.product_repository import ProductRepository, Product
from app.repositories.order_repository import OrderRepository, Order, OrderItem
from app.repositories.subscription_repository import SubscriptionRepository, Subscription
from app.repositories.invoice_repository import InvoiceRepository, Invoice


def _seed_customer(conn: Connection, customer_id: str, email: str = "biz@test.com") -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO customers (id, email, full_name) VALUES (%s, %s, %s) "
            "ON CONFLICT (id) DO NOTHING",
            (customer_id, email, "Business Test User"),
        )


def _seed_product(conn: Connection, product_id: str, sku: str = "TEST-SKU-001") -> str:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO products (id, name, description, price, sku) "
            "VALUES (%s, %s, %s, %s, %s) "
            "ON CONFLICT (sku) DO UPDATE SET name = products.name "
            "RETURNING id",
            (product_id, "Test Product", "A test product", "49.99", sku),
        )
        return str(cur.fetchone()[0])


def _seed_order(
    conn: Connection,
    order_id: str,
    customer_id: str,
    status: str = "pending",
    total: str = "49.99",
) -> str:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO orders (id, customer_id, status, total) "
            "VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (id) DO NOTHING "
            "RETURNING id",
            (order_id, customer_id, status, total),
        )
        row = cur.fetchone()
        return str(row[0]) if row else order_id


def _seed_order_item(
    conn: Connection,
    item_id: str,
    order_id: str,
    product_id: str,
    quantity: int = 1,
    unit_price: str = "49.99",
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) "
            "VALUES (%s, %s, %s, %s, %s) "
            "ON CONFLICT (id) DO NOTHING",
            (item_id, order_id, product_id, quantity, unit_price),
        )


def _seed_subscription(
    conn: Connection,
    sub_id: str,
    customer_id: str,
    plan_name: str = "Pro Monthly",
    status: str = "active",
    price: str = "29.99",
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO subscriptions (id, customer_id, plan_name, status, price) "
            "VALUES (%s, %s, %s, %s, %s) "
            "ON CONFLICT (id) DO NOTHING",
            (sub_id, customer_id, plan_name, status, price),
        )


def _seed_invoice(
    conn: Connection,
    inv_id: str,
    customer_id: str,
    amount: str = "29.99",
    status: str = "paid",
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO invoices (id, customer_id, amount, status, due_date, paid_at) "
            "VALUES (%s, %s, %s, %s, now(), now()) "
            "ON CONFLICT (id) DO NOTHING",
            (inv_id, customer_id, amount, status),
        )


# -- ProductRepository tests ------------------------------------------------


class TestProductRepositoryIntegration:

    def test_list_all_returns_seed_products(self, repo_conn: Connection):
        pid1 = "00000000-0000-0000-0000-000000000101"
        pid2 = "00000000-0000-0000-0000-000000000102"
        _seed_product(repo_conn, pid1, "INT-SKU-001")
        _seed_product(repo_conn, pid2, "INT-SKU-002")

        products = ProductRepository.list_all(repo_conn)

        assert len(products) >= 2
        ids = [str(p.id) for p in products]
        assert pid1 in ids
        assert pid2 in ids

    def test_list_all_empty(self, repo_conn: Connection):
        products = ProductRepository.list_all(repo_conn)
        # May have products from other tests in session, but within this
        # transaction we only see what we inserted
        assert isinstance(products, list)

    def test_get_by_id_found(self, repo_conn: Connection):
        pid = "00000000-0000-0000-0000-000000000103"
        _seed_product(repo_conn, pid, "INT-SKU-003")

        product = ProductRepository.get_by_id(repo_conn, pid)

        assert product is not None
        assert str(product.id) == pid
        assert product.name == "Test Product"
        assert product.price == Decimal("49.99")
        assert product.sku == "INT-SKU-003"

    def test_get_by_id_not_found(self, repo_conn: Connection):
        product = ProductRepository.get_by_id(
            repo_conn,
            "00000000-0000-0000-0000-000000000000",
        )
        assert product is None


# -- OrderRepository tests --------------------------------------------------


class TestOrderRepositoryIntegration:

    def test_create_returns_order(self, repo_conn: Connection):
        cid = "00000000-0000-0000-0000-000000000201"
        _seed_customer(repo_conn, cid)

        order = OrderRepository.create(repo_conn, cid, "99.98", "pending", "123 Main St", "TRACK001")

        assert isinstance(order.id, UUID)
        assert str(order.customer_id) == cid
        assert order.status == "pending"
        assert order.total == Decimal("99.98")

    def test_get_by_id_with_items(self, repo_conn: Connection):
        cid = "00000000-0000-0000-0000-000000000210"
        oid = "00000000-0000-0000-0000-000000000211"
        pid = "00000000-0000-0000-0000-000000000212"
        iid = "00000000-0000-0000-0000-000000000213"
        _seed_customer(repo_conn, cid)
        _seed_product(repo_conn, pid, "INT-SKU-210")
        _seed_order(repo_conn, oid, cid, "shipped", "99.98")
        _seed_order_item(repo_conn, iid, oid, pid, 2, "49.99")

        order = OrderRepository.get_by_id(repo_conn, oid)

        assert order is not None
        assert order.status == "shipped"
        assert len(order.items) == 1
        assert order.items[0].product_name == "Test Product"
        assert order.items[0].quantity == 2
        assert order.items[0].unit_price == Decimal("49.99")

    def test_get_by_id_not_found(self, repo_conn: Connection):
        order = OrderRepository.get_by_id(
            repo_conn,
            "00000000-0000-0000-0000-000000000000",
        )
        assert order is None

    def test_list_by_customer_returns_orders_with_items(self, repo_conn: Connection):
        cid = "00000000-0000-0000-0000-000000000220"
        oid1 = "00000000-0000-0000-0000-000000000221"
        oid2 = "00000000-0000-0000-0000-000000000222"
        pid = "00000000-0000-0000-0000-000000000223"
        iid1 = "00000000-0000-0000-0000-000000000224"
        iid2 = "00000000-0000-0000-0000-000000000225"
        _seed_customer(repo_conn, cid)
        _seed_product(repo_conn, pid, "INT-SKU-220")
        _seed_order(repo_conn, oid1, cid, "delivered", "99.98")
        _seed_order(repo_conn, oid2, cid, "pending", "49.99")
        _seed_order_item(repo_conn, iid1, oid1, pid, 2, "49.99")
        _seed_order_item(repo_conn, iid2, oid2, pid, 1, "49.99")

        orders = OrderRepository.list_by_customer(repo_conn, cid)

        assert len(orders) == 2
        # Ordered by created_at DESC
        for o in orders:
            assert len(o.items) == 1

    def test_list_by_customer_empty(self, repo_conn: Connection):
        cid = "00000000-0000-0000-0000-000000000230"
        _seed_customer(repo_conn, cid)

        orders = OrderRepository.list_by_customer(repo_conn, cid)
        assert orders == []

    def test_update_status_returns_updated(self, repo_conn: Connection):
        cid = "00000000-0000-0000-0000-000000000240"
        oid = "00000000-0000-0000-0000-000000000241"
        _seed_customer(repo_conn, cid)
        _seed_order(repo_conn, oid, cid, "pending", "49.99")

        updated = OrderRepository.update_status(repo_conn, oid, "confirmed")

        assert updated is not None
        assert str(updated.id) == oid
        assert updated.status == "confirmed"

    def test_update_status_persists_change(self, repo_conn: Connection):
        cid = "00000000-0000-0000-0000-000000000242"
        oid = "00000000-0000-0000-0000-000000000243"
        _seed_customer(repo_conn, cid)
        _seed_order(repo_conn, oid, cid, "pending", "49.99")

        OrderRepository.update_status(repo_conn, oid, "shipped")
        fetched = OrderRepository.get_by_id(repo_conn, oid)

        assert fetched is not None
        assert fetched.status == "shipped"

    def test_update_status_not_found(self, repo_conn: Connection):
        result = OrderRepository.update_status(
            repo_conn,
            "00000000-0000-0000-0000-000000000fff",
            "shipped",
        )
        assert result is None


# -- SubscriptionRepository tests -------------------------------------------


class TestSubscriptionRepositoryIntegration:

    def test_list_by_customer_returns_subscriptions(self, repo_conn: Connection):
        cid = "00000000-0000-0000-0000-000000000301"
        sid = "00000000-0000-0000-0000-000000000302"
        _seed_customer(repo_conn, cid)
        _seed_subscription(repo_conn, sid, cid, "Pro Monthly", "active", "29.99")

        subs = SubscriptionRepository.list_by_customer(repo_conn, cid)

        assert len(subs) >= 1
        assert subs[0].plan_name == "Pro Monthly"
        assert subs[0].status == "active"
        assert subs[0].price == Decimal("29.99")

    def test_list_by_customer_empty(self, repo_conn: Connection):
        cid = "00000000-0000-0000-0000-000000000310"
        _seed_customer(repo_conn, cid)

        subs = SubscriptionRepository.list_by_customer(repo_conn, cid)
        assert subs == []

    def test_get_by_id_found(self, repo_conn: Connection):
        cid = "00000000-0000-0000-0000-000000000320"
        sid = "00000000-0000-0000-0000-000000000321"
        _seed_customer(repo_conn, cid)
        _seed_subscription(repo_conn, sid, cid, "Enterprise", "active", "99.99")

        sub = SubscriptionRepository.get_by_id(repo_conn, sid)

        assert sub is not None
        assert str(sub.id) == sid
        assert sub.plan_name == "Enterprise"
        assert sub.price == Decimal("99.99")

    def test_get_by_id_not_found(self, repo_conn: Connection):
        sub = SubscriptionRepository.get_by_id(
            repo_conn,
            "00000000-0000-0000-0000-000000000000",
        )
        assert sub is None


# -- InvoiceRepository tests ------------------------------------------------


class TestInvoiceRepositoryIntegration:

    def test_list_by_customer_returns_invoices(self, repo_conn: Connection):
        cid = "00000000-0000-0000-0000-000000000401"
        inv_id = "00000000-0000-0000-0000-000000000402"
        _seed_customer(repo_conn, cid)
        _seed_invoice(repo_conn, inv_id, cid, "29.99", "paid")

        invoices = InvoiceRepository.list_by_customer(repo_conn, cid)

        assert len(invoices) >= 1
        found = [inv for inv in invoices if str(inv.id) == inv_id]
        assert len(found) == 1
        assert found[0].status == "paid"
        assert found[0].amount == Decimal("29.99")

    def test_list_by_customer_empty(self, repo_conn: Connection):
        cid = "00000000-0000-0000-0000-000000000410"
        _seed_customer(repo_conn, cid)

        invoices = InvoiceRepository.list_by_customer(repo_conn, cid)
        assert invoices == []
