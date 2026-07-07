from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import Connection

from app.api.auth import check_ownership, get_current_user
from app.api.deps import DbDep, LlmClientDep, TicketServiceDep
from app.api.schemas import ChatRequest, ChatResponse
from app.graph.state import SupportState
from app.graph.workflow import run_graph
from app.llm.provider import LLMClientError
from app.repositories.conversation_repository import ConversationRepository
from app.services.ticket_service import TicketService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/messages", response_model=ChatResponse)
def send_message(
    body: ChatRequest,
    db: DbDep,
    current_user: Annotated[dict, Depends(get_current_user)],
    llm: LlmClientDep,
    ticket_service: TicketServiceDep,
):
    ticket_id = body.ticket_id
    if ticket_id:
        ticket = ticket_service.get_ticket(db, ticket_id)
        if ticket is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found",
            )
        check_ownership(current_user, ticket.customer_id)
    else:
        ticket = ticket_service.create_ticket(
            db, str(current_user["id"]), "Chat support", "normal"
        )
        ticket_id = str(ticket.id)

    ConversationRepository.append_message(db, ticket_id, "customer", body.message)

    initial_state = SupportState(
        ticket_id=ticket_id,
        customer_id=str(current_user["id"]),
        customer_message=body.message,
    )

    try:
        result = run_graph(initial_state, llm=llm, conn=db)
    except LLMClientError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service unavailable: {e}",
        )

    ConversationRepository.append_message(
        db, ticket_id, "ai", result["final_response"]
    )

    db.commit()

    return ChatResponse(
        ticket_id=ticket_id,
        response=result["final_response"],
        escalated=result["escalate"],
        escalation_reason=result.get("escalation_reason"),
    )
