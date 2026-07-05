"""
JWT helpers: encode/decode a token, get_current_user() dependency,
and require_role() dependency used to gate agent-only routes.
Deliberately simple — 2 roles, no permission matrix.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from psycopg import Connection

from app.api.deps import get_db
from app.config import JWT_ALGORITHM, JWT_EXPIRY_HOURS, JWT_SECRET

security = HTTPBearer()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(customer_id: int, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)
    payload = {"sub": str(customer_id), "role": role, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def get_current_user(
    token: Annotated[str, Depends(security)],
    db: Annotated[Connection, Depends(get_db)],
) -> dict:
    payload = decode_access_token(token)
    customer_id: str = payload.get("sub")
    role: str = payload.get("role")
    if customer_id is None or role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    with db.cursor() as cur:
        cur.execute(
            "SELECT id, email, full_name, role, created_at FROM customers WHERE id = %s",
            (customer_id,),
        )
        row = cur.fetchone()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return {
        "id": row[0],
        "email": row[1],
        "full_name": row[2],
        "role": row[3],
        "created_at": row[4],
    }


def require_role(required_role: str):
    def role_checker(current_user: Annotated[dict, Depends(get_current_user)]):
        if current_user["role"] != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker


# ── Customer helpers (no dedicated repository layer yet) ────────────────

def create_customer(db: Connection, email: str, full_name: str, password: str) -> int:
    hashed = hash_password(password)
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO customers (email, full_name, password_hash) "
            "VALUES (%s, %s, %s) RETURNING id",
            (email, full_name, hashed),
        )
        row = cur.fetchone()
    db.commit()
    return row[0]


def get_customer_by_email(db: Connection, email: str) -> dict | None:
    with db.cursor() as cur:
        cur.execute(
            "SELECT id, email, full_name, password_hash, role, created_at "
            "FROM customers WHERE email = %s",
            (email,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return {
        "id": row[0],
        "email": row[1],
        "full_name": row[2],
        "password_hash": row[3],
        "role": row[4],
        "created_at": row[5],
    }
