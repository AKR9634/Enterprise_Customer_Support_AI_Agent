"""
Account specialist: fills the shared skeleton with an account-focused
role description and references customer profile, addresses, and
authentication metadata from business_data.
"""

from __future__ import annotations

from typing import Any

from app.graph.agents.specialist_skeleton import render_generic_agent_prompt

__all__ = [
    "render_account_prompt",
]

ACCOUNT_ROLE = (
    "You are an account management specialist. "
    "You handle profile updates, password resets, account security, and preferences. "
    "When business_data contains customer profile or account fields, refer to them directly."
)


def render_account_prompt(
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
        role_description=ACCOUNT_ROLE,
    )
