"""Integration tests for auth endpoints: register -> login -> refresh -> me."""

from collections.abc import Generator

import jwt
import pytest
from fastapi.testclient import TestClient
from psycopg import Connection

from app.config import JWT_ALGORITHM, JWT_SECRET, TEST_DATABASE_URL
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
def client(db_conn: Connection) -> Generator[TestClient, None, None]:
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
    body = {"email": "alice@example.com", "full_name": "Alice", "password": "P@ssw0rd!"}
    res = client.post("/auth/register", json=body)
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    return {"token": data["access_token"], "email": body["email"]}


class TestAuthRegister:

    def test_register_returns_jwt(self, client: TestClient) -> None:
        body = {"email": "bob@example.com", "full_name": "Bob", "password": "Str0ng!pass"}
        res = client.post("/auth/register", json=body)
        assert res.status_code == 201
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        payload = jwt.decode(data["access_token"], JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert payload["role"] == "customer"
        assert isinstance(payload["sub"], str)

    def test_register_duplicate_email(self, client: TestClient, registered_user: dict) -> None:
        body = {"email": registered_user["email"], "full_name": "Alice", "password": "P@ssw0rd!"}
        res = client.post("/auth/register", json=body)
        assert res.status_code == 409
        assert "already registered" in res.json()["detail"].lower()


class TestAuthLogin:

    def test_login_success(self, client: TestClient, registered_user: dict) -> None:
        body = {"email": registered_user["email"], "password": "P@ssw0rd!"}
        res = client.post("/auth/login", json=body)
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data

    def test_login_wrong_password(self, client: TestClient, registered_user: dict) -> None:
        body = {"email": registered_user["email"], "password": "wrong-password"}
        res = client.post("/auth/login", json=body)
        assert res.status_code == 401
        assert "invalid" in res.json()["detail"].lower()

    def test_login_nonexistent_user(self, client: TestClient) -> None:
        body = {"email": "nobody@example.com", "password": "anything"}
        res = client.post("/auth/login", json=body)
        assert res.status_code == 401


class TestAuthRefresh:

    def test_refresh_returns_new_token(self, client: TestClient, registered_user: dict) -> None:
        res = client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["access_token"] != registered_user["token"]

    def test_refresh_without_token_returns_401(self, client: TestClient) -> None:
        res = client.post("/auth/refresh")
        assert res.status_code == 401


class TestAuthMe:

    def test_me_returns_profile(self, client: TestClient, registered_user: dict) -> None:
        res = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["email"] == registered_user["email"]
        assert data["role"] == "customer"
        assert "id" in data
        assert "full_name" in data

    def test_me_without_token_returns_401(self, client: TestClient) -> None:
        res = client.get("/auth/me")
        assert res.status_code == 401

    def test_me_with_invalid_token_returns_401(self, client: TestClient) -> None:
        res = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert res.status_code == 401

    def test_me_does_not_expose_password(self, client: TestClient, registered_user: dict) -> None:
        res = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )
        data = res.json()
        assert "password" not in data
        assert "password_hash" not in data
