"""
Pytest fixtures for integration tests against a real test database.
"""

import pytest
from psycopg import Connection

from app.config import TEST_DATABASE_URL
from app.db.session import get_connection


@pytest.fixture(scope="session")
def db_url() -> str:
    assert TEST_DATABASE_URL, "TEST_DATABASE_URL must be set in .env"
    return TEST_DATABASE_URL


@pytest.fixture
def db_conn(db_url: str) -> Connection:
    conn = get_connection(db_url)
    try:
        yield conn
    finally:
        conn.close()
