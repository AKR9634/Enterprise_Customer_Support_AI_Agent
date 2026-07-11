from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import Connection

from app.api.auth import check_ownership, get_current_user
from app.api.deps import ConversationRepoDep, DbDep, TicketServiceDep
from app.api.schemas import (
    ConversationResponse,
    MessageResponse,
    StatusUpdate,
    TicketCreate,
    TicketDetailResponse,
    TicketListResponse,
    TicketMessagesResponse,
    TicketResponse,
)
from app.repositories.conversation_repository import ConversationRepository
from app.services.ticket_service import InvalidTicketTransition, TicketService

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    body: TicketCreate,
    db: DbDep,
    current_user: Annotated[dict, Depends(get_current_user)],
    ticket_service: TicketServiceDep,
):
    ticket = ticket_service.create_ticket(
        db, str(current_user["id"]), body.subject, body.priority
    )
    db.commit()
    return _ticket_to_response(ticket)


@router.get("", response_model=TicketListResponse)
def list_tickets(
    db: DbDep,
    current_user: Annotated[dict, Depends(get_current_user)],
    ticket_service: TicketServiceDep,
):
    tickets = ticket_service.list_tickets(db, current_user)
    return TicketListResponse(tickets=[_ticket_to_response(t) for t in tickets])


@router.get("/{ticket_id}", response_model=TicketDetailResponse)
def get_ticket(
    ticket_id: str,
    db: DbDep,
    current_user: Annotated[dict, Depends(get_current_user)],
    ticket_service: TicketServiceDep,
    conversation_repo: ConversationRepoDep,
):
    ticket = ticket_service.get_ticket(db, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    check_ownership(current_user, ticket.customer_id)

    messages = conversation_repo.list_by_ticket(db, ticket_id)
    return TicketDetailResponse(
        ticket=_ticket_to_response(ticket),
        conversation=ConversationResponse(
            messages=[MessageResponse(**{
                "id": str(m.id),
                "ticket_id": str(m.ticket_id),
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at,
            }) for m in messages]
        ),
    )


@router.get("/{ticket_id}/messages", response_model=TicketMessagesResponse)
def get_ticket_messages(
    ticket_id: str,
    db: DbDep,
    current_user: Annotated[dict, Depends(get_current_user)],
    ticket_service: TicketServiceDep,
    conversation_repo: ConversationRepoDep,
):
    ticket = ticket_service.get_ticket(db, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    check_ownership(current_user, ticket.customer_id)

    messages = conversation_repo.list_by_ticket(db, ticket_id)
    return TicketMessagesResponse(
        ticket_id=ticket_id,
        messages=[
            MessageResponse(
                id=str(m.id),
                ticket_id=str(m.ticket_id),
                role=m.role,
                content=m.content,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )


@router.patch("/{ticket_id}/status", response_model=TicketResponse)
def update_ticket_status(
    ticket_id: str,
    body: StatusUpdate,
    db: DbDep,
    current_user: Annotated[dict, Depends(get_current_user)],
    ticket_service: TicketServiceDep,
):
    ticket = ticket_service.get_ticket(db, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    check_ownership(current_user, ticket.customer_id)

    try:
        updated = ticket_service.transition_status(db, ticket_id, body.status)
    except InvalidTicketTransition as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    db.commit()
    return _ticket_to_response(updated)


# ── Helpers ──────────────────────────────────────────────────────────────

def _ticket_to_response(ticket) -> TicketResponse:
    return TicketResponse(
        id=str(ticket.id),
        customer_id=str(ticket.customer_id),
        subject=ticket.subject,
        status=ticket.status,
        priority=ticket.priority,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )
