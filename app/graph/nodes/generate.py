"""
Node 6 — Response Generation. Dispatches to the specialist agent
selected by the Supervisor (Node 5) and calls the LLM to produce
draft_response.
"""

from __future__ import annotations

from typing import Any

from app.graph.agents.account_agent import render_account_prompt
from app.graph.agents.billing_agent import render_billing_prompt
from app.graph.agents.general_agent import render_general_prompt
from app.graph.agents.order_agent import render_order_prompt
from app.graph.agents.product_agent import render_product_prompt
from app.graph.state import SupportState
from app.llm.provider import LLMClient

__all__ = [
    "GenerateNode",
]

_SPECIALIST_REGISTRY: dict[str, Any] = {
    "billing": render_billing_prompt,
    "order": render_order_prompt,
    "account": render_account_prompt,
    "product": render_product_prompt,
    "general": render_general_prompt,
}


class GenerateNode:
    """Graph node that drafts a response using the LLM and the
    assembled context (knowledge base, business data, history).

    Dispatches to the specialist prompt renderer indicated by
    state["active_agent"], falling back to general if the agent
    name is unknown.
    """

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm or LLMClient()

    def __call__(self, state: SupportState) -> dict[str, Any]:
        agent = state.get("active_agent", "general")
        render_prompt = _SPECIALIST_REGISTRY.get(agent, render_general_prompt)

        prompt = render_prompt(
            customer_message=state.get("customer_message", ""),
            conversation_history=state.get("conversation_history"),
            retrieved_docs=state.get("retrieved_docs"),
            business_data=state.get("business_data"),
        )

        draft = self._llm.generate(prompt)

        return {"draft_response": draft}
