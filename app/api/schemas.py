"""
All Pydantic request/response models in one file: tickets, chat
messages, escalations, and auth payloads. Kept as a single module
since the project is small enough that per-domain files add
navigation overhead without real benefit.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr


# ── Auth ────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    created_at: datetime
