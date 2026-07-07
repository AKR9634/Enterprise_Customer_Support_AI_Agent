"""
Integration tests for EscalationRepository against a real test database.
Every test runs inside a transaction that is rolled back on teardown.
"""

from uuid import UUID

from psycopg import Connection

from app.repositories.escalation_repository import EscalationRepository, Escalation


def _seed_customer(conn: Connection, customer_id: str, email: str = "a@b.com") -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO customers (id, email, full_name) VALUES (%s, %s, %s)",
            (customer_id, email, "Test User"),
        )


def _seed_ticket(conn: Connection, ticket_id: str, customer_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO tickets (id, customer_id, subject, status, priority) "
            "VALUES (%s, %s, %s, %s, %s)",
            (ticket_id, customer_id, "Test ticket", "open", "normal"),
        )


def _count_escalations(conn: Connection) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM escalations")
        return cur.fetchone()[0]


class TestEscalationRepository:

    def test_create_returns_escalation(self, repo_conn: Connection):
        cust_id = "00000000-0000-0000-0000-000000000001"
        ticket_id = "00000000-0000-0000-0000-000000000010"
        _seed_customer(repo_conn, cust_id)
        _seed_ticket(repo_conn, ticket_id, cust_id)

        esc = EscalationRepository.create(
            repo_conn, ticket_id, "Low confidence",
            category="billing", confidence=0.35,
            customer_message="Where is my refund?",
            draft_response="We are looking into it.",
        )

        assert isinstance(esc.id, UUID)
        assert esc.ticket_id == UUID(ticket_id)
        assert esc.status == "queued"
        assert esc.priority == "normal"
        assert esc.escalation_reason == "Low confidence"
        assert esc.category == "billing"
        assert esc.confidence == 0.35
        assert esc.customer_message == "Where is my refund?"
        assert esc.draft_response == "We are looking into it."

    def test_create_persists_row(self, repo_conn: Connection):
        cust_id = "00000000-0000-0000-0000-000000000002"
        ticket_id = "00000000-0000-0000-0000-000000000020"
        _seed_customer(repo_conn, cust_id)
        _seed_ticket(repo_conn, ticket_id, cust_id)

        EscalationRepository.create(repo_conn, ticket_id, "Test")
        assert _count_escalations(repo_conn) == 1

        EscalationRepository.create(repo_conn, ticket_id, "Test 2")
        assert _count_escalations(repo_conn) == 2

    def test_get_by_id_found(self, repo_conn: Connection):
        cust_id = "00000000-0000-0000-0000-000000000003"
        ticket_id = "00000000-0000-0000-0000-000000000030"
        _seed_customer(repo_conn, cust_id)
        _seed_ticket(repo_conn, ticket_id, cust_id)

        created = EscalationRepository.create(repo_conn, ticket_id, "Find me")
        fetched = EscalationRepository.get_by_id(repo_conn, str(created.id))

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.ticket_id == created.ticket_id
        assert fetched.escalation_reason == created.escalation_reason

    def test_get_by_id_not_found(self, repo_conn: Connection):
        result = EscalationRepository.get_by_id(
            repo_conn,
            "00000000-0000-0000-0000-000000000000",
        )
        assert result is None

    def test_list_queued_returns_pending_only(self, repo_conn: Connection):
        cust_id = "00000000-0000-0000-0000-000000000004"
        ticket_id = "00000000-0000-0000-0000-000000000040"
        _seed_customer(repo_conn, cust_id)
        _seed_ticket(repo_conn, ticket_id, cust_id)

        EscalationRepository.create(repo_conn, ticket_id, "Queued 1")
        e2 = EscalationRepository.create(repo_conn, ticket_id, "Queued 2")

        EscalationRepository.update_status(repo_conn, str(e2.id), "resolved")

        queued = EscalationRepository.list_queued(repo_conn)
        assert len(queued) == 1
        assert queued[0].escalation_reason == "Queued 1"

    def test_list_queued_ordered_by_priority_then_age(self, repo_conn: Connection):
        cust_id = "00000000-0000-0000-0000-000000000005"
        t1 = "00000000-0000-0000-0000-000000000051"
        t2 = "00000000-0000-0000-0000-000000000052"
        t3 = "00000000-0000-0000-0000-000000000053"
        _seed_customer(repo_conn, cust_id)
        for tid in (t1, t2, t3):
            _seed_ticket(repo_conn, tid, cust_id)

        EscalationRepository.create(repo_conn, t1, "Low pri", priority="low")
        EscalationRepository.create(repo_conn, t2, "Urgent", priority="urgent")
        EscalationRepository.create(repo_conn, t3, "High pri", priority="high")

        queued = EscalationRepository.list_queued(repo_conn)
        assert len(queued) == 3
        assert queued[0].escalation_reason == "Urgent"
        assert queued[1].escalation_reason == "High pri"
        assert queued[2].escalation_reason == "Low pri"

    def test_update_status_returns_updated(self, repo_conn: Connection):
        cust_id = "00000000-0000-0000-0000-000000000006"
        ticket_id = "00000000-0000-0000-0000-000000000060"
        _seed_customer(repo_conn, cust_id)
        _seed_ticket(repo_conn, ticket_id, cust_id)

        created = EscalationRepository.create(repo_conn, ticket_id, "Status change")
        updated = EscalationRepository.update_status(repo_conn, str(created.id), "in_review")

        assert updated is not None
        assert updated.id == created.id
        assert updated.status == "in_review"

    def test_update_status_persists_change(self, repo_conn: Connection):
        cust_id = "00000000-0000-0000-0000-000000000007"
        ticket_id = "00000000-0000-0000-0000-000000000070"
        _seed_customer(repo_conn, cust_id)
        _seed_ticket(repo_conn, ticket_id, cust_id)

        created = EscalationRepository.create(repo_conn, ticket_id, "Check persist")
        EscalationRepository.update_status(repo_conn, str(created.id), "resolved")

        fetched = EscalationRepository.get_by_id(repo_conn, str(created.id))
        assert fetched is not None
        assert fetched.status == "resolved"

    def test_assign_reviewer_updates_assigned_reviewer(self, repo_conn: Connection):
        cust_id = "00000000-0000-0000-0000-000000000008"
        agent_id = "00000000-0000-0000-0000-000000000080"
        ticket_id = "00000000-0000-0000-0000-000000000081"
        _seed_customer(repo_conn, cust_id)
        _seed_customer(repo_conn, agent_id, "agent@test.com")
        _seed_ticket(repo_conn, ticket_id, cust_id)

        created = EscalationRepository.create(repo_conn, ticket_id, "Assign me")
        updated = EscalationRepository.assign_reviewer(repo_conn, str(created.id), agent_id)

        assert updated is not None
        assert updated.id == created.id
        assert updated.assigned_reviewer == UUID(agent_id)

    def test_assign_reviewer_conflict(self, repo_conn: Connection):
        cust_id = "00000000-0000-0000-0000-000000000009"
        agent_a = "00000000-0000-0000-0000-000000000090"
        agent_b = "00000000-0000-0000-0000-000000000091"
        ticket_id = "00000000-0000-0000-0000-000000000092"
        _seed_customer(repo_conn, cust_id)
        _seed_customer(repo_conn, agent_a, "agent_a@test.com")
        _seed_customer(repo_conn, agent_b, "agent_b@test.com")
        _seed_ticket(repo_conn, ticket_id, cust_id)

        created = EscalationRepository.create(repo_conn, ticket_id, "Conflict test")

        EscalationRepository.assign_reviewer(repo_conn, str(created.id), agent_a)
        EscalationRepository.assign_reviewer(repo_conn, str(created.id), agent_b)

        fetched = EscalationRepository.get_by_id(repo_conn, str(created.id))
        assert fetched is not None
        assert fetched.assigned_reviewer == UUID(agent_b)
