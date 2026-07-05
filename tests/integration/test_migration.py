"""
Integration tests for the SQL migration runner (0001_init.sql).
"""

import pytest
from psycopg import Connection

from scripts.migrate import migrate, _applied_files, MIGRATIONS_DIR


def _table_exists(conn: Connection, table: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)",
            (table,),
        )
        return cur.fetchone()[0]


class TestMigration:
    def test_migration_creates_all_tables(self, db_conn: Connection, db_url: str):
        """First run creates schema_migrations, customers, tickets, conversations."""
        # Clean slate: drop tracking table so we can re-apply
        with db_conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS conversations, tickets, customers, schema_migrations CASCADE")
        db_conn.commit()

        migrate(db_url)

        assert _table_exists(db_conn, "schema_migrations")
        assert _table_exists(db_conn, "customers")
        assert _table_exists(db_conn, "tickets")
        assert _table_exists(db_conn, "conversations")

    def test_migration_is_idempotent(self, db_conn: Connection, db_url: str):
        """Second run applies zero new files."""
        # Ensure tables exist from prior test or setup
        with db_conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS conversations, tickets, customers, schema_migrations CASCADE")
        db_conn.commit()

        migrate(db_url)
        applied_second = migrate(db_url)

        assert applied_second == [], f"Expected no new migrations on second run, got: {applied_second}"

    def test_tracking_table_records_applied(self, db_conn: Connection, db_url: str):
        """schema_migrations contains the applied file after migration."""
        with db_conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS conversations, tickets, customers, schema_migrations CASCADE")
        db_conn.commit()

        migrate(db_url)
        applied = _applied_files(db_conn)
        assert "0001_init.sql" in applied

    def test_foreign_key_enforced_customer(self, db_conn: Connection, db_url: str):
        """Inserting a ticket with non-existent customer_id raises FK violation."""
        with db_conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS conversations, tickets, customers, schema_migrations CASCADE")
        db_conn.commit()

        migrate(db_url)

        with pytest.raises(Exception) as excinfo:
            with db_conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO tickets (id, customer_id, subject, status) "
                    "VALUES (gen_random_uuid(), gen_random_uuid(), 'test', 'open')"
                )
            db_conn.commit()
        assert "violates foreign key" in str(excinfo.value).lower()

    def test_foreign_key_enforced_ticket(self, db_conn: Connection, db_url: str):
        """Inserting a conversation with non-existent ticket_id raises FK violation."""
        with db_conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS conversations, tickets, customers, schema_migrations CASCADE")
        db_conn.commit()

        migrate(db_url)

        with pytest.raises(Exception) as excinfo:
            with db_conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO conversations (id, ticket_id, role, content) "
                    "VALUES (gen_random_uuid(), gen_random_uuid(), 'customer', 'hello')"
                )
            db_conn.commit()
        assert "violates foreign key" in str(excinfo.value).lower()

    def test_valid_insert_chain(self, db_conn: Connection, db_url: str):
        """Insert a customer -> ticket -> conversation and verify the chain."""
        with db_conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS conversations, tickets, customers, schema_migrations CASCADE")
        db_conn.commit()

        migrate(db_url)

        with db_conn.cursor() as cur:
            cur.execute(
                "INSERT INTO customers (id, email, full_name) "
                "VALUES ('a0000000-0000-0000-0000-000000000001', 'a@b.com', 'Alice')"
            )
            cur.execute(
                "INSERT INTO tickets (id, customer_id, subject, status) "
                "VALUES ('b0000000-0000-0000-0000-000000000001', "
                "'a0000000-0000-0000-0000-000000000001', 'Test ticket', 'open')"
            )
            cur.execute(
                "INSERT INTO conversations (id, ticket_id, role, content) "
                "VALUES ('c0000000-0000-0000-0000-000000000001', "
                "'b0000000-0000-0000-0000-000000000001', 'customer', 'Hello!')"
            )
        db_conn.commit()

        with db_conn.cursor() as cur:
            cur.execute("SELECT full_name FROM customers WHERE id = 'a0000000-0000-0000-0000-000000000001'")
            assert cur.fetchone()[0] == "Alice"

            cur.execute("SELECT subject FROM tickets WHERE id = 'b0000000-0000-0000-0000-000000000001'")
            assert cur.fetchone()[0] == "Test ticket"

            cur.execute("SELECT content FROM conversations WHERE id = 'c0000000-0000-0000-0000-000000000001'")
            assert cur.fetchone()[0] == "Hello!"

    def test_status_check_constraint(self, db_conn: Connection, db_url: str):
        """Inserting a ticket with invalid status raises CHECK constraint violation."""
        with db_conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS conversations, tickets, customers, schema_migrations CASCADE")
        db_conn.commit()

        migrate(db_url)

        with db_conn.cursor() as cur:
            cur.execute(
                "INSERT INTO customers (id, email, full_name) "
                "VALUES ('a0000000-0000-0000-0000-000000000002', 'b@c.com', 'Bob')"
            )
        db_conn.commit()

        with pytest.raises(Exception) as excinfo:
            with db_conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO tickets (customer_id, subject, status) "
                    "VALUES ('a0000000-0000-0000-0000-000000000002', 'bad', 'invalid_status')"
                )
            db_conn.commit()
        assert "violates check constraint" in str(excinfo.value).lower() or "check" in str(excinfo.value).lower()

    def test_priority_check_constraint(self, db_conn: Connection, db_url: str):
        """Inserting a ticket with invalid priority raises CHECK constraint violation."""
        with db_conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS conversations, tickets, customers, schema_migrations CASCADE")
        db_conn.commit()

        migrate(db_url)

        with db_conn.cursor() as cur:
            cur.execute(
                "INSERT INTO customers (id, email, full_name) "
                "VALUES ('a0000000-0000-0000-0000-000000000003', 'c@d.com', 'Carol')"
            )
        db_conn.commit()

        with pytest.raises(Exception) as excinfo:
            with db_conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO tickets (customer_id, subject, status, priority) "
                    "VALUES ('a0000000-0000-0000-0000-000000000003', 'bad priority', 'open', 'invalid_priority')"
                )
            db_conn.commit()
        assert "violates check constraint" in str(excinfo.value).lower() or "check" in str(excinfo.value).lower()

    def test_role_check_constraint(self, db_conn: Connection, db_url: str):
        """Inserting a conversation with invalid role raises CHECK constraint violation."""
        with db_conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS conversations, tickets, customers, schema_migrations CASCADE")
        db_conn.commit()

        migrate(db_url)

        with db_conn.cursor() as cur:
            cur.execute(
                "INSERT INTO customers (id, email, full_name) "
                "VALUES ('a0000000-0000-0000-0000-000000000004', 'd@e.com', 'Dave')"
            )
            cur.execute(
                "INSERT INTO tickets (id, customer_id, subject, status) "
                "VALUES ('b0000000-0000-0000-0000-000000000002', "
                "'a0000000-0000-0000-0000-000000000004', 'role test', 'open')"
            )
        db_conn.commit()

        with pytest.raises(Exception) as excinfo:
            with db_conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO conversations (ticket_id, role, content) "
                    "VALUES ('b0000000-0000-0000-0000-000000000002', 'alien', 'test')"
                )
            db_conn.commit()
        assert "violates check constraint" in str(excinfo.value).lower() or "check" in str(excinfo.value).lower()
