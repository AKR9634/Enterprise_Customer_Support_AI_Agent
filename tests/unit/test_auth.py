"""Unit tests for JWT helpers, password hashing, and require_role."""

from unittest.mock import MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException

from app.api.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    require_role,
    verify_password,
)
from app.config import JWT_ALGORITHM, JWT_SECRET


class TestPasswordHashing:

    def test_hash_and_verify_roundtrip(self) -> None:
        password = "secureP@ss123"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self) -> None:
        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_hash_is_different_each_time(self) -> None:
        password = "same-password"
        h1 = hash_password(password)
        h2 = hash_password(password)
        assert h1 != h2
        assert verify_password(password, h1) is True
        assert verify_password(password, h2) is True


class TestJWT:

    def test_create_and_decode(self) -> None:
        token = create_access_token(customer_id=1, role="customer")
        payload = decode_access_token(token)
        assert payload["sub"] == "1"
        assert payload["role"] == "customer"
        assert "exp" in payload

    def test_decode_agent_token(self) -> None:
        token = create_access_token(customer_id=42, role="agent")
        payload = decode_access_token(token)
        assert payload["sub"] == "42"
        assert payload["role"] == "agent"

    def test_decode_invalid_token_raises_401(self) -> None:
        with pytest.raises(HTTPException) as exc:
            decode_access_token("invalid-token")
        assert exc.value.status_code == 401

    def test_decode_expired_token_raises_401(self) -> None:
        payload = {"sub": 1, "role": "customer", "exp": 0}
        expired = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        with pytest.raises(HTTPException) as exc:
            decode_access_token(expired)
        assert exc.value.status_code == 401

    def test_token_carries_sub_role_exp_claims(self) -> None:
        token = create_access_token(customer_id=7, role="agent")
        payload = decode_access_token(token)
        assert set(payload.keys()) == {"sub", "role", "exp"}


class TestRequireRole:

    def test_allows_correct_role(self) -> None:
        checker = require_role("agent")
        result = checker({"role": "agent", "id": 1})
        assert result["role"] == "agent"

    def test_rejects_wrong_role_with_403(self) -> None:
        checker = require_role("agent")
        with pytest.raises(HTTPException) as exc:
            checker({"role": "customer", "id": 1})
        assert exc.value.status_code == 403
        assert "Insufficient permissions" in exc.value.detail

    def test_allows_customer_role(self) -> None:
        checker = require_role("customer")
        result = checker({"role": "customer", "id": 1})
        assert result["role"] == "customer"

    def test_rejects_agent_for_customer_route(self) -> None:
        checker = require_role("customer")
        with pytest.raises(HTTPException) as exc:
            checker({"role": "agent", "id": 1})
        assert exc.value.status_code == 403
