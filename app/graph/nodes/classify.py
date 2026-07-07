"""
Node 1 — Intent Classification. Calls the LLM to categorize the
customer's message as billing / order / account / product / general,
writing category and intent_confidence onto the state.
"""

from __future__ import annotations

from app.graph.state import SupportState
from app.llm.provider import LLMClient

__all__ = [
    "CATEGORIES",
    "ClassifyNode",
]

CATEGORIES = ["billing", "order", "account", "product", "general"]


class ClassifyNode:
    """Graph node that classifies a customer message into one of the
    predefined support categories using an LLM call."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm or LLMClient()

    def __call__(self, state: SupportState) -> dict:
        message = state.get("customer_message", "")
        if not message:
            return {"category": None, "intent_confidence": None}

        category = self._llm.classify(message, CATEGORIES)
        return {
            "category": category,
            "intent_confidence": 0.95,
        }
