from __future__ import annotations

from typing import Any

from psycopg import Connection

from app.repositories.account_metadata_repository import AccountMetadataRepository
from app.repositories.customer_address_repository import CustomerAddressRepository


class AccountService:

    @staticmethod
    def get_customer_profile(conn: Connection, customer_id: str) -> dict[str, Any]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, email, full_name, role, created_at FROM customers WHERE id = %s",
                (customer_id,),
            )
            row = cur.fetchone()
            if row is None:
                return {}
            return {
                "id": str(row[0]),
                "email": row[1],
                "full_name": row[2],
                "role": row[3],
                "created_at": row[4].isoformat(),
            }

    @staticmethod
    def get_customer_addresses(conn: Connection, customer_id: str) -> list[dict[str, Any]]:
        addresses = CustomerAddressRepository.list_by_customer(conn, customer_id)
        return [
            {
                "id": str(a.id),
                "label": a.label,
                "street": a.street,
                "city": a.city,
                "state": a.state,
                "zip": a.zip,
                "country": a.country,
                "is_default": a.is_default,
            }
            for a in addresses
        ]

    @staticmethod
    def get_account_metadata(conn: Connection, customer_id: str) -> dict[str, Any]:
        meta = AccountMetadataRepository.get_by_customer(conn, customer_id)
        if meta is None:
            return {}
        return {
            "email_verified": meta.email_verified,
            "phone_verified": meta.phone_verified,
            "two_factor_enabled": meta.two_factor_enabled,
            "account_locked": meta.account_locked,
            "last_login_at": meta.last_login_at.isoformat() if meta.last_login_at else None,
        }
