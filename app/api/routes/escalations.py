"""
Agent-facing escalation queue: list queued escalations, claim one,
view its full context (draft answer, retrieved docs, why it was
flagged), and resolve it. Restricted to the 'agent' role.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth import require_role
from app.api.deps import DbDep, EscalationServiceDep
from app.api.schemas import (
    AgentReplyRequest,
    AgentReplyResponse,
    EscalationContextOut,
    EscalationListResponse,
    EscalationOut,
)
from app.repositories.conversation_repository import ConversationRepository
from app.services.escalation_service import EscalationConflictError

router = APIRouter(prefix="/escalations", tags=["escalations"])

AgentDep = Annotated[dict, Depends(require_role("agent"))]


@router.get("", response_model=EscalationListResponse)
def list_escalations(
    db: DbDep,
    agent: AgentDep,
    svc: EscalationServiceDep,
):
    escalations = svc.list_queued(db)
    return EscalationListResponse(
        escalations=[_escalation_to_out(e) for e in escalations]
    )


@router.get("/{escalation_id}/context", response_model=EscalationContextOut)
def escalation_context(
    escalation_id: str,
    db: DbDep,
    agent: AgentDep,
    svc: EscalationServiceDep,
):
    escalation = svc.get_by_id(db, escalation_id)
    if escalation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Escalation not found",
        )
    return EscalationContextOut(
        escalation_id=str(escalation.id),
        ticket_id=str(escalation.ticket_id),
        customer_message=escalation.customer_message,
        draft_response=escalation.draft_response,
        routing_reason=escalation.routing_reason,
        escalation_reason=escalation.escalation_reason,
        category=escalation.category,
        confidence=escalation.confidence,
        retrieved_docs=escalation.retrieved_docs,
        business_data=escalation.business_data,
    )


@router.post("/{escalation_id}/claim", response_model=EscalationOut)
def claim_escalation(
    escalation_id: str,
    db: DbDep,
    agent: AgentDep,
    svc: EscalationServiceDep,
):
    try:
        escalation = svc.claim(db, escalation_id, str(agent["id"]))
    except EscalationConflictError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Escalation already claimed or not found",
        )
    db.commit()
    return _escalation_to_out(escalation)


@router.post("/{escalation_id}/resolve", response_model=EscalationOut)
def resolve_escalation(
    escalation_id: str,
    db: DbDep,
    agent: AgentDep,
    svc: EscalationServiceDep,
):
    try:
        escalation = svc.resolve(db, escalation_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Escalation not found",
        )
    db.commit()
    return _escalation_to_out(escalation)


@router.post("/{escalation_id}/reply", response_model=AgentReplyResponse)
def agent_reply(
    escalation_id: str,
    body: AgentReplyRequest,
    db: DbDep,
    agent: AgentDep,
    svc: EscalationServiceDep,
):
    escalation = svc.get_by_id(db, escalation_id)
    if escalation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Escalation not found",
        )

    ConversationRepository.append_message(
        db, str(escalation.ticket_id), "agent", body.message,
    )
    svc.resolve(db, escalation_id)
    db.commit()
    return AgentReplyResponse(
        escalation_id=escalation_id,
        ticket_id=str(escalation.ticket_id),
        status="resolved",
    )


# ── Helpers ──────────────────────────────────────────────────────────────

def _escalation_to_out(escalation) -> EscalationOut:
    return EscalationOut(
        id=str(escalation.id),
        ticket_id=str(escalation.ticket_id),
        status=escalation.status,
        priority=escalation.priority,
        assigned_reviewer=str(escalation.assigned_reviewer)
            if escalation.assigned_reviewer else None,
        escalation_reason=escalation.escalation_reason,
        category=escalation.category,
        confidence=escalation.confidence,
        customer_message=escalation.customer_message,
        draft_response=escalation.draft_response,
        routing_reason=escalation.routing_reason,
        created_at=escalation.created_at,
        updated_at=escalation.updated_at,
    )
