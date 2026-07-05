"""
Integration tests for ConversationRepository against a real test database.
Every test runs inside a transaction that is rolled back on teardown.
"""

from uuid import UUID

import pytest
from psycopg import Connection

from app.repositories.conversation_repository import (
    ConversationRepository,
    ConversationMessage,
)


def _seed_customer(conn: Connection, customer_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO customers (id, email, full_name) VALUES (%s, %s, %s)",
            (customer_id, "c@d.com", "Charlie"),
        )


def _seed_ticket(conn: Connection, ticket_id: str, customer_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO tickets (id, customer_id, subject, status) "
            "VALUES (%s, %s, %s, %s)",
            (ticket_id, customer_id, "Test ticket", "open"),
        )


class TestConversationRepository:

    def test_append_message_returns_message(self, repo_conn: Connection):
        customer_id = "00000000-0000-0000-0000-000000000100"
        ticket_id = "00000000-0000-0000-0000-000000000101"
        _seed_customer(repo_conn, customer_id)
        _seed_ticket(repo_conn, ticket_id, customer_id)

        msg = ConversationRepository.append_message(
            repo_conn, ticket_id, "customer", "Hello, I need help!",
        )

        assert isinstance(msg.id, UUID)
        assert msg.ticket_id == UUID(ticket_id)
        assert msg.role == "customer"
        assert msg.content == "Hello, I need help!"

    def test_append_message_persists(self, repo_conn: Connection):
        customer_id = "00000000-0000-0000-0000-000000000102"
        ticket_id = "00000000-0000-0000-0000-000000000103"
        _seed_customer(repo_conn, customer_id)
        _seed_ticket(repo_conn, ticket_id, customer_id)

        ConversationRepository.append_message(
            repo_conn, ticket_id, "customer", "Message one",
        )
        ConversationRepository.append_message(
            repo_conn, ticket_id, "ai", "Message two",
        )

        with repo_conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM conversations WHERE ticket_id = %s",
                (ticket_id,),
            )
            assert cur.fetchone()[0] == 2

    def test_list_by_ticket_ordered_asc(self, repo_conn: Connection):
        customer_id = "00000000-0000-0000-0000-000000000104"
        ticket_id = "00000000-0000-0000-0000-000000000105"
        _seed_customer(repo_conn, customer_id)
        _seed_ticket(repo_conn, ticket_id, customer_id)

        m1 = ConversationRepository.append_message(
            repo_conn, ticket_id, "customer", "First",
        )
        m2 = ConversationRepository.append_message(
            repo_conn, ticket_id, "ai", "Second",
        )
        m3 = ConversationRepository.append_message(
            repo_conn, ticket_id, "customer", "Third",
        )

        messages = ConversationRepository.list_by_ticket(repo_conn, ticket_id)

        assert len(messages) == 3
        assert messages[0].id == m1.id
        assert messages[1].id == m2.id
        assert messages[2].id == m3.id

    def test_list_by_ticket_empty(self, repo_conn: Connection):
        customer_id = "00000000-0000-0000-0000-000000000106"
        ticket_id = "00000000-0000-0000-0000-000000000107"
        _seed_customer(repo_conn, customer_id)
        _seed_ticket(repo_conn, ticket_id, customer_id)

        messages = ConversationRepository.list_by_ticket(repo_conn, ticket_id)
        assert messages == []

    def test_list_by_ticket_scoped_to_ticket(self, repo_conn: Connection):
        customer_id = "00000000-0000-0000-0000-000000000108"
        ticket_a = "00000000-0000-0000-0000-000000000109"
        ticket_b = "00000000-0000-0000-0000-000000000110"
        _seed_customer(repo_conn, customer_id)
        _seed_ticket(repo_conn, ticket_a, customer_id)
        _seed_ticket(repo_conn, ticket_b, customer_id)

        ConversationRepository.append_message(repo_conn, ticket_a, "customer", "A1")
        ConversationRepository.append_message(repo_conn, ticket_b, "customer", "B1")
        ConversationRepository.append_message(repo_conn, ticket_b, "ai", "B2")

        msgs_a = ConversationRepository.list_by_ticket(repo_conn, ticket_a)
        msgs_b = ConversationRepository.list_by_ticket(repo_conn, ticket_b)

        assert len(msgs_a) == 1
        assert len(msgs_b) == 2

    def test_append_message_fk_violation(self, repo_conn: Connection):
        with pytest.raises(Exception) as excinfo:
            ConversationRepository.append_message(
                repo_conn,
                "00000000-0000-0000-0000-000000000fff",
                "customer",
                "orphan message",
            )
        assert "violates foreign key" in str(excinfo.value).lower()

    def test_append_message_invalid_role(self, repo_conn: Connection):
        customer_id = "00000000-0000-0000-0000-000000000111"
        ticket_id = "00000000-0000-0000-0000-000000000112"
        _seed_customer(repo_conn, customer_id)
        _seed_ticket(repo_conn, ticket_id, customer_id)

        with pytest.raises(Exception) as excinfo:
            ConversationRepository.append_message(
                repo_conn, ticket_id, "alien", "bad role",
            )
        assert "violates check constraint" in str(excinfo.value).lower() or "check" in str(
            excinfo.value
        ).lower()
