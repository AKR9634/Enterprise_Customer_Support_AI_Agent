from contextlib import contextmanager
from typing import Generator, Optional

import psycopg
from psycopg import Connection

from app.config import DATABASE_URL


def get_connection(db_url: Optional[str] = None) -> Connection:
    url = db_url or DATABASE_URL
    return psycopg.connect(url)


@contextmanager
def get_connection_ctx(db_url: Optional[str] = None) -> Generator[Connection, None, None]:
    conn = get_connection(db_url)
    try:
        yield conn
    finally:
        conn.close()
