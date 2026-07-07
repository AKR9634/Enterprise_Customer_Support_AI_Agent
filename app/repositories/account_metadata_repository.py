from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from psycopg import Connection


@dataclass
class AccountMetadata:
    id: UUID
    customer_id: UUID
    email_verified: bool
    phone_verified: bool
    two_factor_enabled: bool
    account_locked: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


_COLUMNS = [
    "id", "customer_id", "email_verified", "phone_verified",
    "two_factor_enabled", "account_locked", "last_login_at",
    "created_at", "updated_at",
]


def _row_to_metadata(row: tuple) -> AccountMetadata:
    return AccountMetadata(**dict(zip(_COLUMNS, row)))


class AccountMetadataRepository:

    @staticmethod
    def get_by_customer(conn: Connection, customer_id: str) -> Optional[AccountMetadata]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM account_metadata WHERE customer_id = %s",
                (customer_id,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return _row_to_metadata(row)
