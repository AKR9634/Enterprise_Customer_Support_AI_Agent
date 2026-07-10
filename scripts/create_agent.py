"""
Creates a new agent user in the database.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import get_connection
from app.config import DATABASE_URL
from app.api.auth import hash_password


def create_agent(email: str, full_name: str, password: str) -> dict:
    conn = get_connection(DATABASE_URL)
    try:
        hashed = hash_password(password)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM customers WHERE email = %s",
                (email,),
            )
            existing = cur.fetchone()
            if existing:
                print(f"Agent with email {email} already exists (id={existing[0]}). Skipping.")
                return {"id": str(existing[0]), "email": email, "full_name": full_name, "role": "agent"}

            cur.execute(
                "INSERT INTO customers (email, full_name, password_hash, role) "
                "VALUES (%s, %s, %s, 'agent') RETURNING id, email, full_name, role, created_at",
                (email, full_name, hashed),
            )
            row = cur.fetchone()
        conn.commit()
        return {
            "id": str(row[0]), "email": row[1],
            "full_name": row[2], "role": row[3],
            "created_at": row[4],
        }
    finally:
        conn.close()


if __name__ == "__main__":
    agent = create_agent("jack@company.com", "Jack Agent", "123")
    print(f"\nAgent created successfully!")
    print(f"  ID:        {agent['id']}")
    print(f"  Email:     {agent['email']}")
    print(f"  Name:      {agent['full_name']}")
    print(f"  Role:      {agent['role']}")
    print(f"  Password:  123")
    print(f"\nLogin at http://localhost:3000/auth/login")
