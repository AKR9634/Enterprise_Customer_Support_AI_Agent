"""
Auth endpoints: register, login, and refresh. Issues a JWT carrying
the customer_id and role claim ('customer' or 'agent') used by
every other protected route.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import Connection

from app.api.auth import (
    create_access_token,
    create_customer,
    decode_access_token,
    get_current_user,
    get_customer_by_email,
    verify_password,
)
from app.api.deps import DbDep
from app.api.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: DbDep):
    existing = get_customer_by_email(db, body.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    customer_id = create_customer(db, body.email, body.full_name, body.password)
    token = create_access_token(customer_id, "customer")
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: DbDep):
    customer = get_customer_by_email(db, body.email)
    if customer is None or not verify_password(body.password, customer["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token(customer["id"], customer["role"])
    return TokenResponse(access_token=token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(current_user: Annotated[dict, Depends(get_current_user)]):
    token = create_access_token(current_user["id"], current_user["role"])
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def me(current_user: Annotated[dict, Depends(get_current_user)]):
    return UserResponse(**current_user)
