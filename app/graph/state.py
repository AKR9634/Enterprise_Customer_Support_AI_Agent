from typing import TypedDict


class SupportState(TypedDict, total=False):
    """State object threaded through every LangGraph node.

    Each node reads the fields it needs and writes the fields it
    produces; LangGraph merges partial updates as it runs.
    """

    ticket_id: str
    customer_id: str
    customer_message: str
    conversation_history: list[dict]
    category: str | None
    intent_confidence: float | None
    retrieved_docs: list[dict] | None
    business_data: dict | None
    active_agent: str | None
    routing_reason: str | None
    draft_response: str | None
    grounding_ok: bool | None
    confidence: float | None
    escalate: bool
    escalation_reason: str | None
    final_response: str | None
