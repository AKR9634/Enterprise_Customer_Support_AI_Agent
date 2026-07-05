"""
Populates the database with sample customers and tickets
exercising the state machine. Run after migrations.
"""

import psycopg
from app.config import DATABASE_URL
from app.services.ticket_service import TicketService

conn = psycopg.connect(DATABASE_URL)

customers = [
    ("alice@example.com", "Alice Johnson"),
    ("bob@example.com", "Bob Smith"),
    ("carol@example.com", "Carol Davis"),
]
customer_ids = []
for email, name in customers:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO customers (email, full_name) VALUES (%s, %s) "
            "ON CONFLICT (email) DO NOTHING RETURNING id",
            (email, name),
        )
        row = cur.fetchone()
        if row:
            cid = row[0]
        else:
            cur.execute("SELECT id FROM customers WHERE email = %s", (email,))
            cid = cur.fetchone()[0]
        customer_ids.append(cid)
    print(f"Customer: {name} ({email}) -> {cid}")

conn.commit()

tickets_data = [
    (customer_ids[0], "Where is my order?", "high"),
    (customer_ids[0], "Refund request for order #1234", "normal"),
    (customer_ids[1], "Login not working", "urgent"),
    (customer_ids[1], "Change shipping address", "low"),
    (customer_ids[2], "Billing question about invoice", "normal"),
]
ticket_ids = []
for cid, subject, priority in tickets_data:
    t = TicketService.create_ticket(conn, str(cid), subject, priority)
    ticket_ids.append(t.id)
    print(f"Ticket: {subject} ({t.status}, {t.priority}) -> {t.id}")

conn.commit()

t1 = TicketService.transition_status(conn, str(ticket_ids[0]), "pending")
print(f"Ticket 0 -> {t1.status}")

t2 = TicketService.transition_status(conn, str(ticket_ids[1]), "pending")
t2 = TicketService.transition_status(conn, str(ticket_ids[1]), "resolved")
print(f"Ticket 1 -> {t2.status}")

t3 = TicketService.transition_status(conn, str(ticket_ids[2]), "pending")
t3 = TicketService.transition_status(conn, str(ticket_ids[2]), "escalated")
print(f"Ticket 2 -> {t3.status}")

conn.commit()
conn.close()

print("\nDone — 3 customers, 5 tickets in various statuses.")
