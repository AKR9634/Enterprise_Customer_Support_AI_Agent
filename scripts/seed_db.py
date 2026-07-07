"""
Populates the local/test database with a couple of sample customers
and tickets so the app is usable immediately after setup.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import DATABASE_URL
from app.db.session import get_connection
from app.repositories.ticket_repository import TicketRepository
from scripts.migrate import migrate


def _seed_customers(conn) -> dict[str, dict]:
    customers = {
        "alice": {
            "email": "alice@example.com",
            "full_name": "Alice Johnson",
            "password_hash": "$2b$12$LJ3m4ys3Lk0TSwHnbfOMiOXPm1QlqQy0n0f0e0d0a0b0c0d0e0f0g0h0i0",
            "role": "customer",
        },
        "bob": {
            "email": "bob@example.com",
            "full_name": "Bob Smith",
            "password_hash": "$2b$12$LJ3m4ys3Lk0TSwHnbfOMiOXPm1QlqQy0n0f0e0d0a0b0c0d0e0f0g0h0i0",
            "role": "agent",
        },
    }
    created = {}
    with conn.cursor() as cur:
        for key, data in customers.items():
            cur.execute(
                "INSERT INTO customers (email, full_name, password_hash, role) "
                "VALUES (%(email)s, %(full_name)s, %(password_hash)s, %(role)s) "
                "ON CONFLICT (email) DO UPDATE SET email = customers.email "
                "RETURNING id, email, full_name, role",
                data,
            )
            row = cur.fetchone()
            created[key] = {"id": str(row[0]), "email": row[1], "full_name": row[2], "role": row[3]}
    conn.commit()
    return created


def _seed_tickets(conn, customers: dict[str, dict]) -> None:
    tickets = [
        {"customer_id": customers["alice"]["id"], "subject": "Order not received", "priority": "high"},
        {"customer_id": customers["alice"]["id"], "subject": "Wrong item shipped", "priority": "normal"},
        {"customer_id": customers["alice"]["id"], "subject": "Billing inquiry about invoice #1234", "priority": "low"},
        {"customer_id": customers["bob"]["id"], "subject": "Test ticket for agent", "priority": "normal"},
    ]
    with conn.cursor() as cur:
        for t in tickets:
            cur.execute(
                "SELECT COUNT(*) FROM tickets WHERE customer_id = %(customer_id)s AND subject = %(subject)s",
                t,
            )
            if cur.fetchone()[0] == 0:
                cur.execute(
                    "INSERT INTO tickets (customer_id, subject, status, priority) "
                    "VALUES ("
                    "%(customer_id)s, %(subject)s, 'open', %(priority)s)",
                    t,
                )

    conn.commit()


def _seed_products(conn) -> dict[str, str]:
    products = [
        {"name": "Widget Pro", "description": "High-performance widget for professionals", "price": "49.99", "sku": "WIDGET-PRO-001"},
        {"name": "Gadget X", "description": "Next-generation gadget with extended battery life", "price": "89.99", "sku": "GADGET-X-002"},
        {"name": "Premium Support Add-on", "description": "24/7 priority support and dedicated account manager", "price": "29.99", "sku": "SUP-PREM-003"},
    ]
    created = {}
    with conn.cursor() as cur:
        for p in products:
            cur.execute(
                "INSERT INTO products (name, description, price, sku) "
                "VALUES (%(name)s, %(description)s, %(price)s, %(sku)s) "
                "ON CONFLICT (sku) DO UPDATE SET name = products.name "
                "RETURNING id, name",
                p,
            )
            row = cur.fetchone()
            created[row[1]] = str(row[0])
    conn.commit()
    return created


def _seed_orders(conn, customer_id: str, products: dict[str, str]) -> None:
    orders = [
        {
            "customer_id": customer_id,
            "status": "delivered",
            "total": "189.97",
            "shipping_address": "123 Main St, Springfield, IL 62701",
            "tracking_number": "1Z999AA10123456784",
            "notes": "Leave at front door",
            "items": [
                {"product_id": products["Widget Pro"], "quantity": 2, "unit_price": "49.99"},
                {"product_id": products["Gadget X"], "quantity": 1, "unit_price": "89.99"},
            ],
        },
        {
            "customer_id": customer_id,
            "status": "pending",
            "total": "49.99",
            "shipping_address": "123 Main St, Springfield, IL 62701",
            "tracking_number": "",
            "notes": "",
            "items": [
                {"product_id": products["Widget Pro"], "quantity": 1, "unit_price": "49.99"},
            ],
        },
    ]
    with conn.cursor() as cur:
        for o in orders:
            cur.execute(
                "SELECT COUNT(*) FROM orders WHERE customer_id = %s AND total = %s AND status = %s",
                (o["customer_id"], o["total"], o["status"]),
            )
            if cur.fetchone()[0] > 0:
                continue

            cur.execute(
                "INSERT INTO orders (customer_id, status, total, shipping_address, tracking_number, notes) "
                "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                (o["customer_id"], o["status"], o["total"], o["shipping_address"], o["tracking_number"], o["notes"]),
            )
            order_id = cur.fetchone()[0]

            for item in o["items"]:
                cur.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, unit_price) "
                    "VALUES (%s, %s, %s, %s)",
                    (order_id, item["product_id"], item["quantity"], item["unit_price"]),
                )
    conn.commit()


def _seed_subscriptions(conn, customers: dict[str, dict]) -> None:
    subs = [
        {
            "customer_id": customers["alice"]["id"],
            "plan_name": "Pro Monthly",
            "status": "active",
            "price": "29.99",
        },
        {
            "customer_id": customers["bob"]["id"],
            "plan_name": "Enterprise Monthly",
            "status": "active",
            "price": "99.99",
        },
    ]
    with conn.cursor() as cur:
        for s in subs:
            cur.execute(
                "SELECT COUNT(*) FROM subscriptions WHERE customer_id = %s AND plan_name = %s",
                (s["customer_id"], s["plan_name"]),
            )
            if cur.fetchone()[0] > 0:
                continue

            cur.execute(
                "INSERT INTO subscriptions (customer_id, plan_name, status, price) "
                "VALUES (%s, %s, %s, %s) RETURNING id",
                (s["customer_id"], s["plan_name"], s["status"], s["price"]),
            )
    conn.commit()


def _seed_invoices(conn, customers: dict[str, dict]) -> None:
    import datetime as dt

    invoices = [
        {
            "customer_id": customers["alice"]["id"],
            "amount": "29.99",
            "status": "paid",
            "due_date": dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=15),
            "paid_at": dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=10),
        },
        {
            "customer_id": customers["alice"]["id"],
            "amount": "29.99",
            "status": "pending",
            "due_date": dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=15),
            "paid_at": None,
        },
        {
            "customer_id": customers["bob"]["id"],
            "amount": "99.99",
            "status": "paid",
            "due_date": dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=5),
            "paid_at": dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=2),
        },
        {
            "customer_id": customers["bob"]["id"],
            "amount": "99.99",
            "status": "overdue",
            "due_date": dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30),
            "paid_at": None,
        },
    ]
    with conn.cursor() as cur:
        for inv in invoices:
            cur.execute(
                "SELECT COUNT(*) FROM invoices WHERE customer_id = %s AND amount = %s AND due_date = %s",
                (inv["customer_id"], inv["amount"], inv["due_date"]),
            )
            if cur.fetchone()[0] > 0:
                continue

            cur.execute(
                "INSERT INTO invoices (customer_id, amount, status, due_date, paid_at) "
                "VALUES (%s, %s, %s, %s, %s)",
                (inv["customer_id"], inv["amount"], inv["status"], inv["due_date"], inv["paid_at"]),
            )
    conn.commit()


def _seed_addresses(conn, customers: dict[str, dict]) -> None:
    addresses = [
        {
            "customer_id": customers["alice"]["id"],
            "label": "Home",
            "street": "123 Main St",
            "city": "Springfield",
            "state": "IL",
            "zip": "62701",
            "country": "US",
            "is_default": True,
        },
        {
            "customer_id": customers["alice"]["id"],
            "label": "Work",
            "street": "456 Oak Ave",
            "city": "Springfield",
            "state": "IL",
            "zip": "62702",
            "country": "US",
            "is_default": False,
        },
    ]
    with conn.cursor() as cur:
        for a in addresses:
            cur.execute(
                "SELECT COUNT(*) FROM customer_addresses WHERE customer_id = %s AND label = %s",
                (a["customer_id"], a["label"]),
            )
            if cur.fetchone()[0] > 0:
                continue
            cur.execute(
                "INSERT INTO customer_addresses (customer_id, label, street, city, state, zip, country, is_default) "
                "VALUES (%(customer_id)s, %(label)s, %(street)s, %(city)s, %(state)s, %(zip)s, %(country)s, %(is_default)s)",
                a,
            )
    conn.commit()


def _seed_account_metadata(conn, customers: dict[str, dict]) -> None:
    import datetime as dt

    metadata = [
        {
            "customer_id": customers["alice"]["id"],
            "email_verified": True,
            "phone_verified": False,
            "two_factor_enabled": False,
            "account_locked": False,
            "last_login_at": dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1),
        },
        {
            "customer_id": customers["bob"]["id"],
            "email_verified": True,
            "phone_verified": True,
            "two_factor_enabled": True,
            "account_locked": False,
            "last_login_at": dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=2),
        },
    ]
    with conn.cursor() as cur:
        for m in metadata:
            cur.execute(
                "SELECT COUNT(*) FROM account_metadata WHERE customer_id = %s",
                (m["customer_id"],),
            )
            if cur.fetchone()[0] > 0:
                continue
            cur.execute(
                "INSERT INTO account_metadata (customer_id, email_verified, phone_verified, two_factor_enabled, account_locked, last_login_at) "
                "VALUES (%(customer_id)s, %(email_verified)s, %(phone_verified)s, %(two_factor_enabled)s, %(account_locked)s, %(last_login_at)s)",
                m,
            )
    conn.commit()


def _seed_product_specs(conn, products: dict[str, str]) -> None:
    specs = [
        {"product_name": "Widget Pro", "key": "Dimensions", "value": "10 x 5 x 2 inches"},
        {"product_name": "Widget Pro", "key": "Weight", "value": "1.2 lbs"},
        {"product_name": "Widget Pro", "key": "Material", "value": "Aluminum alloy"},
        {"product_name": "Widget Pro", "key": "Color", "value": "Space Gray"},
        {"product_name": "Gadget X", "key": "Battery Life", "value": "24 hours"},
        {"product_name": "Gadget X", "key": "Weight", "value": "0.8 lbs"},
        {"product_name": "Gadget X", "key": "Connectivity", "value": "Bluetooth 5.0, Wi-Fi 6"},
        {"product_name": "Gadget X", "key": "Water Resistance", "value": "IP68"},
    ]
    with conn.cursor() as cur:
        for s in specs:
            product_id = products.get(s["product_name"])
            if not product_id:
                continue
            cur.execute(
                "SELECT COUNT(*) FROM product_specifications WHERE product_id = %s AND key = %s",
                (product_id, s["key"]),
            )
            if cur.fetchone()[0] > 0:
                continue
            cur.execute(
                "INSERT INTO product_specifications (product_id, key, value) VALUES (%s, %s, %s)",
                (product_id, s["key"], s["value"]),
            )
    conn.commit()


def _seed_warranties(conn, products: dict[str, str]) -> None:
    warranties = [
        {"product_name": "Widget Pro", "duration_months": 12, "terms": "Covers defects in materials and workmanship. Does not cover misuse or unauthorized modifications."},
        {"product_name": "Gadget X", "duration_months": 24, "terms": "Covers manufacturing defects and battery degradation beyond 20% capacity. Water damage not covered."},
        {"product_name": "Premium Support Add-on", "duration_months": 0, "terms": "Service add-on — no separate warranty. Coverage tied to active subscription period."},
    ]
    with conn.cursor() as cur:
        for w in warranties:
            product_id = products.get(w["product_name"])
            if not product_id:
                continue
            cur.execute(
                "SELECT COUNT(*) FROM product_warranties WHERE product_id = %s",
                (product_id,),
            )
            if cur.fetchone()[0] > 0:
                continue
            cur.execute(
                "INSERT INTO product_warranties (product_id, duration_months, terms) VALUES (%s, %s, %s)",
                (product_id, w["duration_months"], w["terms"]),
            )
    conn.commit()


def _seed_inventory(conn, products: dict[str, str]) -> None:
    inventory = [
        {"product_name": "Widget Pro", "stock_count": 150, "low_stock": 20},
        {"product_name": "Gadget X", "stock_count": 8, "low_stock": 15},
        {"product_name": "Premium Support Add-on", "stock_count": 9999, "low_stock": 100},
    ]
    with conn.cursor() as cur:
        for i in inventory:
            product_id = products.get(i["product_name"])
            if not product_id:
                continue
            cur.execute(
                "SELECT COUNT(*) FROM inventory WHERE product_id = %s",
                (product_id,),
            )
            if cur.fetchone()[0] > 0:
                continue
            cur.execute(
                "INSERT INTO inventory (product_id, stock_count, low_stock) VALUES (%s, %s, %s)",
                (product_id, i["stock_count"], i["low_stock"]),
            )
    conn.commit()


def seed() -> None:
    print("Running migrations...")
    migrate(DATABASE_URL)

    print("Seeding customers...")
    conn = get_connection(DATABASE_URL)
    try:
        customers = _seed_customers(conn)
        for key, data in customers.items():
            print(f"  {key}: {data['email']} ({data['role']})")

        print("Seeding tickets...")
        _seed_tickets(conn, customers)
        print("  Done.")

        print("Seeding products...")
        products = _seed_products(conn)
        for name in products:
            print(f"  {name}")

        print("Seeding orders...")
        _seed_orders(conn, customers["alice"]["id"], products)
        print("  Done.")

        print("Seeding subscriptions...")
        _seed_subscriptions(conn, customers)
        print("  Done.")

        print("Seeding invoices...")
        _seed_invoices(conn, customers)
        print("  Done.")

        print("Seeding addresses...")
        _seed_addresses(conn, customers)
        print("  Done.")

        print("Seeding account metadata...")
        _seed_account_metadata(conn, customers)
        print("  Done.")

        print("Seeding product specifications...")
        _seed_product_specs(conn, products)
        print("  Done.")

        print("Seeding warranties...")
        _seed_warranties(conn, products)
        print("  Done.")

        print("Seeding inventory...")
        _seed_inventory(conn, products)
        print("  Done.")
    finally:
        conn.close()


if __name__ == "__main__":
    seed()
