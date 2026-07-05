"""
Seeds one dummy customer into the database for manual testing.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.api.auth import create_customer, hash_password
from app.db.session import get_connection
from app.config import DATABASE_URL

USERS = [
    ("alice@example.com", "Alice Johnson", "Password123!"),
    ("bob@example.com", "Bob Smith", "Password123!"),
    ("carol@example.com", "Carol Davis", "Password123!"),
    ("jack@example.com", "Jack Toromto", "Password123!"),
]

conn = get_connection(DATABASE_URL)
try:
    with conn.cursor() as cur:
        cur.execute("SELECT id, email, full_name FROM customers")
        rows = cur.fetchall()
        print("Existing customers:")
        for r in rows:
            print(f"  #{r[0]}: {r[1]} ({r[2]})")

    for email, full_name, password in USERS:
        hashed = hash_password(password)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM customers WHERE email = %s",
                (email,),
            )
            existing = cur.fetchone()

        if existing:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE customers SET password_hash = %s WHERE id = %s",
                    (hashed, existing[0]),
                )
            print(f"Updated password for {email}")
        else:
            cid = create_customer(conn, email, full_name, password)
            print(f"Created {email} as customer #{cid}")

    print(f"\nAll users share password: Password123!")
    print("Emails:", ", ".join(u[0] for u in USERS))
finally:
    conn.close()
