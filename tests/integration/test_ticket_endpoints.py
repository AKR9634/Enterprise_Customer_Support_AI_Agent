"""Integration tests for ticket CRUD and status PATCH endpoints."""

from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from psycopg import Connection

from app.api.auth import create_access_token, hash_password
from app.config import TEST_DATABASE_URL
from app.db.session import get_connection
from app.main import app
from scripts.migrate import migrate


@pytest.fixture(scope="session")
def db_url() -> str:
    return TEST_DATABASE_URL


@pytest.fixture(scope="session")
def _run_migrations(db_url: str) -> None:
    migrate(db_url)


@pytest.fixture
def db_conn(db_url: str) -> Generator[Connection, None, None]:
    conn = get_connection(db_url)
    conn.autocommit = False
    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()


@pytest.fixture
def client(db_conn: Connection, _run_migrations: None) -> Generator[TestClient, None, None]:
    app.dependency_overrides.clear()

    def override_get_db() -> Generator[Connection, None, None]:
        yield db_conn

    from app.api.deps import get_db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def registered_user(client: TestClient) -> dict:
    email = f"user-{uuid4()}@example.com"
    body = {"email": email, "full_name": "Alice", "password": "P@ssw0rd!"}
    res = client.post("/auth/register", json=body)
    assert res.status_code == 201, res.json()
    data = res.json()
    assert "access_token" in data
    return {"token": data["access_token"], "email": body["email"]}


@pytest.fixture
def agent_user(client: TestClient, db_conn: Connection) -> dict:
    email = f"agent-{uuid4()}@example.com"
    hashed = hash_password("AgentP@ss1")
    with db_conn.cursor() as cur:
        cur.execute(
            "INSERT INTO customers (email, full_name, password_hash, role) "
            "VALUES (%s, %s, %s, 'agent') RETURNING id",
            (email, "Agent User", hashed),
        )
        customer_id = cur.fetchone()[0]
    db_conn.commit()
    token = create_access_token(int(customer_id) if isinstance(customer_id, int) else str(customer_id), "agent")
    return {"token": token, "email": email, "id": str(customer_id)}


@pytest.fixture
def created_ticket(client: TestClient, registered_user: dict) -> dict:
    res = client.post(
        "/tickets",
        json={"subject": "Test ticket", "priority": "high"},
        headers={"Authorization": f"Bearer {registered_user['token']}"},
    )
    assert res.status_code == 201
    return res.json()


class TestCreateTicket:

    def test_create_ticket_returns_201(self, client: TestClient, registered_user: dict) -> None:
        res = client.post(
            "/tickets",
            json={"subject": "My order is late"},
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["subject"] == "My order is late"
        assert data["status"] == "open"
        assert data["priority"] == "normal"
        assert "id" in data
        assert "customer_id" in data
        assert "created_at" in data

    def test_create_ticket_custom_priority(self, client: TestClient, registered_user: dict) -> None:
        res = client.post(
            "/tickets",
            json={"subject": "Urgent issue", "priority": "urgent"},
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )
        assert res.status_code == 201
        assert res.json()["priority"] == "urgent"

    def test_create_ticket_requires_auth(self, client: TestClient) -> None:
        res = client.post("/tickets", json={"subject": "No auth"})
        assert res.status_code == 401

    def test_create_ticket_sets_customer_id_from_jwt(self, client: TestClient, registered_user: dict) -> None:
        import jwt as pyjwt

        from app.config import JWT_ALGORITHM, JWT_SECRET

        payload = pyjwt.decode(
            registered_user["token"], JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )
        expected_customer_id = payload["sub"]

        res = client.post(
            "/tickets",
            json={"subject": "Who owns me?"},
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )
        assert res.status_code == 201
        assert res.json()["customer_id"] == expected_customer_id


class TestListTickets:

    def test_list_returns_own_tickets(self, client: TestClient, registered_user: dict) -> None:
        label_a = f"ticket-a-{uuid4()}"
        label_b = f"ticket-b-{uuid4()}"
        client.post(
            "/tickets",
            json={"subject": label_a},
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )
        client.post(
            "/tickets",
            json={"subject": label_b},
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )

        res = client.get(
            "/tickets",
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )
        assert res.status_code == 200
        data = res.json()
        subjects = {t["subject"] for t in data["tickets"]}
        assert label_a in subjects
        assert label_b in subjects

    def test_list_returns_all_for_agent(self, client: TestClient, registered_user: dict, agent_user: dict) -> None:
        ticket_label = f"agent-view-{uuid4()}"
        client.post(
            "/tickets",
            json={"subject": ticket_label},
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )

        res = client.get(
            "/tickets",
            headers={"Authorization": f"Bearer {agent_user['token']}"},
        )
        assert res.status_code == 200
        data = res.json()
        customer_tickets = [t for t in data["tickets"] if t["subject"] == ticket_label]
        assert len(customer_tickets) == 1

    def test_list_requires_auth(self, client: TestClient) -> None:
        res = client.get("/tickets")
        assert res.status_code == 401

    def test_list_empty_for_new_user(self, client: TestClient) -> None:
        email = f"empty-{uuid4()}@example.com"
        body = {"email": email, "full_name": "New", "password": "Pass1234!"}
        res = client.post("/auth/register", json=body)
        assert res.status_code == 201, res.json()
        token = res.json()["access_token"]

        res = client.get(
            "/tickets",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.json()["tickets"] == []


class TestGetTicket:

    def test_get_ticket_returns_detail(self, client: TestClient, registered_user: dict, created_ticket: dict) -> None:
        res = client.get(
            f"/tickets/{created_ticket['id']}",
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["ticket"]["id"] == created_ticket["id"]
        assert data["ticket"]["subject"] == created_ticket["subject"]
        assert "conversation" in data
        assert data["conversation"]["messages"] == []

    def test_get_ticket_404_for_nonexistent(self, client: TestClient, registered_user: dict) -> None:
        res = client.get(
            "/tickets/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )
        assert res.status_code == 404

    def test_get_other_customers_ticket_returns_404(self, client: TestClient, registered_user: dict, created_ticket: dict) -> None:
        email = f"other-{uuid4()}@example.com"
        body = {"email": email, "full_name": "Other", "password": "Pass1234!"}
        res = client.post("/auth/register", json=body)
        assert res.status_code == 201, res.json()
        other_token = res.json()["access_token"]

        res = client.get(
            f"/tickets/{created_ticket['id']}",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert res.status_code == 404

    def test_agent_can_get_any_ticket(self, client: TestClient, agent_user: dict, created_ticket: dict) -> None:
        res = client.get(
            f"/tickets/{created_ticket['id']}",
            headers={"Authorization": f"Bearer {agent_user['token']}"},
        )
        assert res.status_code == 200
        assert res.json()["ticket"]["id"] == created_ticket["id"]

    def test_get_ticket_requires_auth(self, client: TestClient, created_ticket: dict) -> None:
        res = client.get(f"/tickets/{created_ticket['id']}")
        assert res.status_code == 401


class TestUpdateTicketStatus:

    def test_patch_status_success(self, client: TestClient, registered_user: dict, created_ticket: dict) -> None:
        res = client.patch(
            f"/tickets/{created_ticket['id']}/status",
            json={"status": "pending"},
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )
        assert res.status_code == 200
        assert res.json()["status"] == "pending"

    def test_patch_illegal_transition_returns_400(self, client: TestClient, registered_user: dict, created_ticket: dict) -> None:
        res = client.patch(
            f"/tickets/{created_ticket['id']}/status",
            json={"status": "closed"},
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )
        assert res.status_code == 400
        assert "Cannot transition" in res.json()["detail"]

    def test_patch_404_for_nonexistent(self, client: TestClient, registered_user: dict) -> None:
        res = client.patch(
            "/tickets/00000000-0000-0000-0000-000000000000/status",
            json={"status": "pending"},
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )
        assert res.status_code == 404

    def test_patch_other_customers_ticket_returns_404(self, client: TestClient, registered_user: dict, created_ticket: dict) -> None:
        email = f"other2-{uuid4()}@example.com"
        body = {"email": email, "full_name": "Other", "password": "Pass1234!"}
        res = client.post("/auth/register", json=body)
        assert res.status_code == 201, res.json()
        other_token = res.json()["access_token"]

        res = client.patch(
            f"/tickets/{created_ticket['id']}/status",
            json={"status": "pending"},
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert res.status_code == 404

    def test_patch_requires_auth(self, client: TestClient, created_ticket: dict) -> None:
        res = client.patch(
            f"/tickets/{created_ticket['id']}/status",
            json={"status": "pending"},
        )
        assert res.status_code == 401
