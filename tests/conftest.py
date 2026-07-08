import uuid
from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from psycopg import Connection

from app.api.auth import create_access_token
from app.api.deps import get_db
from app.db.session import get_connection
from app.main import app
from app.repositories.ticket_repository import TicketRepository
from app.services.escalation_service import EscalationService

@pytest.fixture
def db() -> Generator[Connection, None, None]:
    conn = get_connection()
    conn.autocommit = True
    yield conn
    conn.close()


@pytest.fixture
def client(db: Connection) -> Generator[TestClient, None, None]:
    def _get_db_override() -> Generator[Connection, None, None]:
        yield db

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _create_user(db: Connection, role: str) -> str:
    user_id = str(uuid.uuid4())
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO customers (id, email, full_name, password_hash, role) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (user_id, f"{role}_{user_id[:8]}@test.com", f"Test {role.title()}", "nohash", role),
        )
    return user_id


@pytest.fixture
def agent_token(db: Connection) -> str:
    return create_access_token(_create_user(db, "agent"), "agent")


@pytest.fixture
def second_agent_token(db: Connection) -> str:
    return create_access_token(_create_user(db, "agent"), "agent")


@pytest.fixture
def customer_token(db: Connection) -> str:
    return create_access_token(_create_user(db, "customer"), "customer")



@pytest.fixture
def seed_ticket_and_escalation(db: Connection) -> dict[str, Any]:
    customer_id = _create_user(db, "customer")

    ticket = TicketRepository.create(db, customer_id, "Test subject", "normal")
    svc = EscalationService()
    escalation = svc.enqueue(
        db,
        ticket_id=str(ticket.id),
        escalation_reason="Low confidence",
        category="general",
        confidence=0.3,
        customer_message="Test message?",
        draft_response="Test draft",
        routing_reason="routed to general",
        retrieved_docs=[{"doc_id": "1", "content": "test doc"}],
        business_data={"key": "value"},
        priority="normal",
    )
    return {"customer_id": customer_id, "ticket": ticket, "escalation": escalation}
