"""
Product specialist: fills the shared skeleton with a product-focused
role description and references product catalog, specifications,
inventory, and warranty information from business_data.
"""

from __future__ import annotations

from typing import Any

from app.graph.agents.specialist_skeleton import render_generic_agent_prompt

__all__ = [
    "render_product_prompt",
]

PRODUCT_ROLE = (
    "You are a product specialist. "
    "You handle product features, specifications, compatibility, pricing, inventory, and warranty. "
    "When business_data contains product catalog or inventory fields, refer to them directly."
)


def render_product_prompt(
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
        role_description=PRODUCT_ROLE,
    )
