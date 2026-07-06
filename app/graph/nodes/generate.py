"""
Node 6 — Response Generation. Renders the selected specialist's
prompt (shared skeleton + role-specific fields) with the assembled
context and calls the LLM to produce draft_response.
"""

from __future__ import annotations

from typing import Any

from app.graph.agents.specialist_skeleton import render_generic_agent_prompt
from app.graph.state import SupportState
from app.llm.provider import LLMClient

__all__ = [
    "GenerateNode",
]


class GenerateNode:
    """Graph node that drafts a response using the LLM and the
    assembled context (knowledge base, business data, history)."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm or LLMClient()

    def __call__(self, state: SupportState) -> dict[str, Any]:
        prompt = render_generic_agent_prompt(
            customer_message=state.get("customer_message", ""),
            conversation_history=state.get("conversation_history"),
            retrieved_docs=state.get("retrieved_docs"),
            business_data=state.get("business_data"),
        )

        draft = self._llm.generate(prompt)

        return {"draft_response": draft}
