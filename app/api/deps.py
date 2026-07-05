"""
FastAPI dependency wiring: builds a DB connection, then constructs
each repository and service from it, so routes just declare
Depends(get_ticket_service) instead of wiring this by hand.
"""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from psycopg import Connection

from app.db.session import get_connection


def get_db() -> Generator[Connection, None, None]:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


DbDep = Annotated[Connection, Depends(get_db)]
