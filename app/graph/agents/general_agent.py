"""
General specialist: handles anything that isn't billing or order-
specific, relying mainly on retrieved_docs rather than account data.
"""

from __future__ import annotations

from typing import Any

from app.graph.agents.specialist_skeleton import render_generic_agent_prompt

__all__ = [
    "render_general_prompt",
]

GENERAL_ROLE = (
    "You are a general customer support agent. "
    "You handle questions that don't fall under billing, order, account, or product categories. "
    "Rely on the retrieved knowledge base docs and available business data."
)


def render_general_prompt(
    *,
    customer_message: str,
    conversation_history: list[dict[str, str]] | None = None,
    retrieved_docs: list[dict[str, Any]] | None = None,
    business_data: dict[str, Any] | None = None,
) -> str:
    return render_generic_agent_prompt(
        customer_message=customer_message,
        conversation_history=conversation_history,
        retrieved_docs=retrieved_docs,
        business_data=business_data,
        role_description=GENERAL_ROLE,
    )
