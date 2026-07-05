"""
Pytest fixtures for integration tests against a real test database.
"""

from collections.abc import Generator

import pytest
from psycopg import Connection

from app.config import DATABASE_URL
from app.db.session import get_connection


@pytest.fixture(scope="session")
def db_url() -> str:
    assert DATABASE_URL, "DATABASE_URL must be set in .env"
    return DATABASE_URL


@pytest.fixture
def db_conn(db_url: str) -> Generator[Connection, None, None]:
    conn = get_connection(db_url)
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
def repo_conn(db_conn: Connection) -> Generator[Connection, None, None]:
    db_conn.autocommit = False
    try:
        yield db_conn
    finally:
        db_conn.rollback()
