"""
Order specialist: fills the shared skeleton with an order-tracking
role description and references order/shipment fields from
business_data.
"""

from __future__ import annotations

from typing import Any

from app.graph.agents.specialist_skeleton import render_generic_agent_prompt

__all__ = [
    "render_order_prompt",
]

ORDER_ROLE = (
    "You are an order management specialist. "
    "You handle order status, shipping, delivery dates, order changes, and cancellations. "
    "When business_data contains order or shipment fields, refer to them directly."
)


def render_order_prompt(
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
        role_description=ORDER_ROLE,
    )
