"""
All Pydantic request/response models in one file: tickets, chat
messages, escalations, and auth payloads. Kept as a single module
since the project is small enough that per-domain files add
navigation overhead without real benefit.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


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
    id: str
    email: str
    full_name: str
    role: str
    created_at: datetime


# ── Tickets ──────────────────────────────────────────────────────────────

class TicketCreate(BaseModel):
    subject: str
    priority: str = "normal"


class TicketResponse(BaseModel):
    id: str
    customer_id: str
    subject: str
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime


class TicketListResponse(BaseModel):
    tickets: list[TicketResponse]


class StatusUpdate(BaseModel):
    status: str


class MessageResponse(BaseModel):
    id: str
    ticket_id: str
    role: str
    content: str
    created_at: datetime


class ConversationResponse(BaseModel):
    messages: list[MessageResponse]


class TicketDetailResponse(BaseModel):
    ticket: TicketResponse
    conversation: ConversationResponse


# ── Chat ─────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    ticket_id: str | None = None


class ChatResponse(BaseModel):
    ticket_id: str
    response: str
    escalated: bool
    escalation_reason: str | None = None


# -- Business Data (orders, billing) ---------------------------------------

class ProductOut(BaseModel):
    id: str
    name: str
    description: str
    price: Decimal
    sku: str


class OrderItemOut(BaseModel):
    id: str
    product_id: str
    product_name: str
    quantity: int
    unit_price: Decimal


class OrderOut(BaseModel):
    id: str
    customer_id: str
    status: str
    total: Decimal
    shipping_address: str
    tracking_number: str
    items: list[OrderItemOut]
    created_at: datetime


class SubscriptionOut(BaseModel):
    id: str
    customer_id: str
    plan_name: str
    status: str
    price: Decimal
    started_at: datetime
    next_billing: datetime | None = None
    cancelled_at: datetime | None = None


class InvoiceOut(BaseModel):
    id: str
    customer_id: str
    amount: Decimal
    status: str
    due_date: datetime
    paid_at: datetime | None = None
