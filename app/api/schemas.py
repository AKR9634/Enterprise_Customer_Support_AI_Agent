"""
All Pydantic request/response models in one file: tickets, chat
messages, escalations, and auth payloads. Kept as a single module
since the project is small enough that per-domain files add
navigation overhead without real benefit.
"""

from datetime import datetime
from decimal import Decimal

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
    citations: list[str] = []
    ticket_status: str = "open"


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


# -- Account / Addresses -------------------------------------------------------

class CustomerProfileOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    created_at: datetime


class AddressOut(BaseModel):
    id: str
    label: str
    street: str
    city: str
    state: str
    zip: str
    country: str
    is_default: bool


class AccountMetadataOut(BaseModel):
    email_verified: bool
    phone_verified: bool
    two_factor_enabled: bool
    account_locked: bool
    last_login_at: datetime | None = None


# -- Products / Catalog --------------------------------------------------------

class ProductSpecOut(BaseModel):
    key: str
    value: str


class ProductWarrantyOut(BaseModel):
    duration_months: int
    terms: str


class InventoryOut(BaseModel):
    stock_count: int
    low_stock: int


class ProductDetailOut(BaseModel):
    id: str
    name: str
    description: str
    price: Decimal
    sku: str
    specifications: list[ProductSpecOut] = []
    warranty: ProductWarrantyOut | None = None
    inventory: InventoryOut | None = None


# ── Escalations ──────────────────────────────────────────────────────────────

class EscalationOut(BaseModel):
    id: str
    ticket_id: str
    status: str
    priority: str
    assigned_reviewer: str | None = None
    escalation_reason: str
    category: str | None = None
    confidence: float | None = None
    customer_message: str | None = None
    draft_response: str | None = None
    routing_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class EscalationDetailOut(EscalationOut):
    retrieved_docs: list[dict] = []
    business_data: dict = {}


class EscalationListResponse(BaseModel):
    escalations: list[EscalationOut]


class AgentReplyRequest(BaseModel):
    message: str = Field(..., min_length=1)


class AgentReplyResponse(BaseModel):
    escalation_id: str
    ticket_id: str
    status: str


class EscalationContextOut(BaseModel):
    escalation_id: str
    ticket_id: str
    customer_message: str | None = None
    draft_response: str | None = None
    routing_reason: str | None = None
    escalation_reason: str
    category: str | None = None
    confidence: float | None = None
    retrieved_docs: list[dict] = []
    business_data: dict = {}
