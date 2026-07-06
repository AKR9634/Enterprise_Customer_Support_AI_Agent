"""Integration tests for POST /chat/messages."""
from collections.abc import Generator
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from psycopg import Connection

from app.api.auth import create_access_token, hash_password
from app.db.session import get_connection
from app.main import app
from scripts.migrate import migrate

TEST_DB_URL = "postgresql://postgres:postgres@localhost:5432/test_enterprise_support"


class MockLLMClient:
    """Default mock: verify passes so no escalation."""

    def __init__(self, model=None):
        self._model = model

    def generate(self, prompt, system_prompt=None):
        if system_prompt and "fact-checker" in system_prompt:
            return "YES"
        return "This is a test response regarding your inquiry."

    def classify(self, prompt, categories):
        return "general"


class EscalationMockLLM(MockLLMClient):
    """Verify fails so escalation triggers."""

    def generate(self, prompt, system_prompt=None):
        return "NO"


@pytest.fixture(scope="session")
def db_url() -> str:
    return TEST_DB_URL


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

    def override_get_llm() -> MockLLMClient:
        return MockLLMClient()

    from app.api.deps import get_db, get_llm_client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_llm_client] = override_get_llm

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
    token = create_access_token(customer_id, "agent")
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


class TestSendMessage:

    def test_send_message_auto_creates_ticket(
        self, client: TestClient, registered_user: dict
    ) -> None:
        with patch("app.rag.retriever.search", return_value=[]):
            res = client.post(
                "/chat/messages",
                json={"message": "I need help with my order"},
                headers={"Authorization": f"Bearer {registered_user['token']}"},
            )
        assert res.status_code == 200
        data = res.json()
        assert "ticket_id" in data
        assert data["response"] == "This is a test response regarding your inquiry."
        assert data["escalated"] is False

    def test_send_message_with_existing_ticket(
        self, client: TestClient, registered_user: dict, created_ticket: dict
    ) -> None:
        with patch("app.rag.retriever.search", return_value=[]):
            res = client.post(
                "/chat/messages",
                json={
                    "message": "Still need help",
                    "ticket_id": created_ticket["id"],
                },
                headers={"Authorization": f"Bearer {registered_user['token']}"},
            )
        assert res.status_code == 200
        data = res.json()
        assert data["ticket_id"] == created_ticket["id"]
        assert data["response"] == "This is a test response regarding your inquiry."

    def test_send_message_requires_auth(self, client: TestClient) -> None:
        res = client.post(
            "/chat/messages",
            json={"message": "No auth message"},
        )
        assert res.status_code == 401

    def test_send_message_nonexistent_ticket_returns_404(
        self, client: TestClient, registered_user: dict
    ) -> None:
        fake_id = "00000000-0000-0000-0000-000000000000"
        res = client.post(
            "/chat/messages",
            json={"message": "Missing ticket", "ticket_id": fake_id},
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )
        assert res.status_code == 404

    def test_send_message_other_users_ticket_returns_404(
        self, client: TestClient, registered_user: dict, created_ticket: dict
    ) -> None:
        email = f"other-{uuid4()}@example.com"
        body = {"email": email, "full_name": "Other", "password": "Pass1234!"}
        res = client.post("/auth/register", json=body)
        assert res.status_code == 201, res.json()
        other_token = res.json()["access_token"]

        res = client.post(
            "/chat/messages",
            json={
                "message": "Not my ticket",
                "ticket_id": created_ticket["id"],
            },
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert res.status_code == 404

    def test_agent_can_send_to_any_ticket(
        self, client: TestClient, agent_user: dict, created_ticket: dict
    ) -> None:
        with patch("app.rag.retriever.search", return_value=[]):
            res = client.post(
                "/chat/messages",
                json={
                    "message": "Agent reply",
                    "ticket_id": created_ticket["id"],
                },
                headers={"Authorization": f"Bearer {agent_user['token']}"},
            )
        assert res.status_code == 200
        assert res.json()["ticket_id"] == created_ticket["id"]

    def test_both_messages_persisted(
        self, client: TestClient, registered_user: dict, created_ticket: dict
    ) -> None:
        with patch("app.rag.retriever.search", return_value=[]):
            client.post(
                "/chat/messages",
                json={
                    "message": "Check persistence",
                    "ticket_id": created_ticket["id"],
                },
                headers={"Authorization": f"Bearer {registered_user['token']}"},
            )

        res = client.get(
            f"/tickets/{created_ticket['id']}",
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )
        assert res.status_code == 200
        messages = res.json()["conversation"]["messages"]
        roles = [m["role"] for m in messages]
        assert "customer" in roles
        assert "ai" in roles
        assert any("persistence" in m["content"] for m in messages if m["role"] == "customer")

    def test_empty_message_returns_422(
        self, client: TestClient, registered_user: dict
    ) -> None:
        res = client.post(
            "/chat/messages",
            json={"message": ""},
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )
        assert res.status_code == 422


class TestSendMessageEscalation:

    def test_escalation_returns_acknowledgment(
        self, client: TestClient, registered_user: dict, db_conn: Connection
    ) -> None:
        from app.api.deps import get_llm_client

        original_override = app.dependency_overrides.get(get_llm_client)

        app.dependency_overrides[get_llm_client] = lambda: EscalationMockLLM()

        try:
            with patch("app.rag.retriever.search", return_value=[]):
                res = client.post(
                    "/chat/messages",
                    json={"message": "Trigger escalation"},
                    headers={"Authorization": f"Bearer {registered_user['token']}"},
                )
        finally:
            if original_override:
                app.dependency_overrides[get_llm_client] = original_override
            else:
                del app.dependency_overrides[get_llm_client]

        assert res.status_code == 200
        data = res.json()
        assert data["escalated"] is True
        assert "Thank you" in data["response"]
        assert data["escalation_reason"] is not None
