"""
Integration tests for TicketRepository against a real test database.
Every test runs inside a transaction that is rolled back on teardown.
"""

from uuid import UUID

from psycopg import Connection

from app.repositories.ticket_repository import TicketRepository, Ticket


def _seed_customer(conn: Connection, customer_id: str, email: str = "a@b.com") -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO customers (id, email, full_name) VALUES (%s, %s, %s)",
            (customer_id, email, "Test User"),
        )


def _count_tickets_for_customer(conn: Connection, customer_id: str) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM tickets WHERE customer_id = %s", (customer_id,))
        return cur.fetchone()[0]


class TestTicketRepository:

    def test_create_returns_ticket(self, repo_conn: Connection):
        customer_id = "00000000-0000-0000-0000-000000000001"
        _seed_customer(repo_conn, customer_id)

        ticket = TicketRepository.create(repo_conn, customer_id, "Test subject")

        assert isinstance(ticket.id, UUID)
        assert ticket.customer_id == UUID(customer_id)
        assert ticket.subject == "Test subject"
        assert ticket.status == "open"
        assert ticket.priority == "normal"

    def test_create_default_priority(self, repo_conn: Connection):
        customer_id = "00000000-0000-0000-0000-000000000002"
        _seed_customer(repo_conn, customer_id)

        ticket = TicketRepository.create(repo_conn, customer_id, "No priority")

        assert ticket.priority == "normal"

    def test_create_persists_row(self, repo_conn: Connection):
        customer_id = "00000000-0000-0000-0000-000000000003"
        _seed_customer(repo_conn, customer_id)

        TicketRepository.create(repo_conn, customer_id, "Persist me")
        assert _count_tickets_for_customer(repo_conn, customer_id) == 1

        TicketRepository.create(repo_conn, customer_id, "Another")
        assert _count_tickets_for_customer(repo_conn, customer_id) == 2

    def test_get_by_id_found(self, repo_conn: Connection):
        customer_id = "00000000-0000-0000-0000-000000000004"
        _seed_customer(repo_conn, customer_id)

        created = TicketRepository.create(repo_conn, customer_id, "Find me")
        fetched = TicketRepository.get_by_id(repo_conn, str(created.id))

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.subject == "Find me"
        assert fetched.customer_id == created.customer_id
        assert fetched.status == created.status
        assert fetched.priority == created.priority

    def test_get_by_id_not_found(self, repo_conn: Connection):
        result = TicketRepository.get_by_id(
            repo_conn,
            "00000000-0000-0000-0000-000000000000",
        )
        assert result is None

    def test_list_by_customer_returns_all(self, repo_conn: Connection):
        customer_a = "00000000-0000-0000-0000-000000000010"
        customer_b = "00000000-0000-0000-0000-000000000011"
        _seed_customer(repo_conn, customer_a, "a@test.com")
        _seed_customer(repo_conn, customer_b, "b@test.com")

        TicketRepository.create(repo_conn, customer_a, "A1")
        TicketRepository.create(repo_conn, customer_a, "A2")
        TicketRepository.create(repo_conn, customer_a, "A3")
        TicketRepository.create(repo_conn, customer_b, "B1")
        TicketRepository.create(repo_conn, customer_b, "B2")

        a_tickets = TicketRepository.list_by_customer(repo_conn, customer_a)
        b_tickets = TicketRepository.list_by_customer(repo_conn, customer_b)

        assert len(a_tickets) == 3
        assert len(b_tickets) == 2

    def test_list_by_customer_ordered_desc(self, repo_conn: Connection):
        customer_id = "00000000-0000-0000-0000-000000000020"
        _seed_customer(repo_conn, customer_id)

        t1 = TicketRepository.create(repo_conn, customer_id, "First")
        t2 = TicketRepository.create(repo_conn, customer_id, "Second")
        t3 = TicketRepository.create(repo_conn, customer_id, "Third")

        tickets = TicketRepository.list_by_customer(repo_conn, customer_id)

        assert len(tickets) == 3
        assert tickets[0].created_at >= tickets[1].created_at
        assert tickets[1].created_at >= tickets[2].created_at

    def test_list_by_customer_empty(self, repo_conn: Connection):
        customer_id = "00000000-0000-0000-0000-000000000030"
        _seed_customer(repo_conn, customer_id)

        tickets = TicketRepository.list_by_customer(repo_conn, customer_id)
        assert tickets == []

    def test_update_status_returns_updated(self, repo_conn: Connection):
        customer_id = "00000000-0000-0000-0000-000000000040"
        _seed_customer(repo_conn, customer_id)

        created = TicketRepository.create(repo_conn, customer_id, "Status change")
        updated = TicketRepository.update_status(repo_conn, str(created.id), "resolved")

        assert updated is not None
        assert updated.id == created.id
        assert updated.status == "resolved"

    def test_update_status_persists_change(self, repo_conn: Connection):
        customer_id = "00000000-0000-0000-0000-000000000041"
        _seed_customer(repo_conn, customer_id)

        created = TicketRepository.create(repo_conn, customer_id, "Check persist")
        TicketRepository.update_status(repo_conn, str(created.id), "closed")

        fetched = TicketRepository.get_by_id(repo_conn, str(created.id))
        assert fetched is not None
        assert fetched.status == "closed"

    def test_update_status_nonexistent(self, repo_conn: Connection):
        result = TicketRepository.update_status(
            repo_conn,
            "00000000-0000-0000-0000-000000000fff",
            "closed",
        )
        assert result is None

    def test_update_status_timestamp_changed(self, repo_conn: Connection):
        customer_id = "00000000-0000-0000-0000-000000000050"
        _seed_customer(repo_conn, customer_id)

        created = TicketRepository.create(repo_conn, customer_id, "Timestamp check")
        updated = TicketRepository.update_status(repo_conn, str(created.id), "pending")

        assert updated is not None
        assert updated.updated_at > created.updated_at or updated.updated_at >= created.updated_at
