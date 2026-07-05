"""
Idempotent SQL migration runner.

Reads .sql files from app/db/migrations/ in numeric order, computes
SHA-256 hash, skips already-applied files (tracked in schema_migrations
table), executes and records each new file.
"""

import hashlib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import DATABASE_URL
from app.db.session import get_connection


MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "app" / "db" / "migrations"


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ensure_tracking_table(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename    TEXT        PRIMARY KEY,
                hash        TEXT        NOT NULL,
                applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """)
    conn.commit()


def _applied_files(conn) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT filename FROM schema_migrations")
        return {row[0] for row in cur.fetchall()}


def _get_sql_files() -> list[Path]:
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    return files


def migrate(db_url: str | None = None) -> list[str]:
    url = db_url or DATABASE_URL
    conn = get_connection(url)
    try:
        _ensure_tracking_table(conn)
        applied = _applied_files(conn)
        applied_new: list[str] = []

        for path in _get_sql_files():
            fname = path.name
            if fname in applied:
                print(f"  SKIP  {fname} (already applied)")
                continue

            sql = path.read_text()
            h = _file_hash(path)

            with conn.cursor() as cur:
                cur.execute(sql)
                cur.execute(
                    "INSERT INTO schema_migrations (filename, hash) VALUES (%s, %s)",
                    (fname, h),
                )
            conn.commit()
            applied_new.append(fname)
            print(f"  APPLY {fname}")

        return applied_new
    finally:
        conn.close()


if __name__ == "__main__":
    print("Running migrations from", MIGRATIONS_DIR)
    applied = migrate()
    if applied:
        print(f"Applied {len(applied)} migration(s): {', '.join(applied)}")
    else:
        print("No new migrations to apply.")
