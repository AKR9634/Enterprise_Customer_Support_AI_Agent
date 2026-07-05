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
    finally:
        conn.close()


if __name__ == "__main__":
    seed()
