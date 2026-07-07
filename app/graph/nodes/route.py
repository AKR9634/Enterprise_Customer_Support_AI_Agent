"""
Node 5 — Supervisor Routing. A narrow, routing-only LLM call that
picks which specialist (billing / order / account / product / general)
should answer, given the category and a one-line summary of retrieved
context.
"""

from __future__ import annotations

import logging
from typing import Any

from app.graph.agents.supervisor_prompt import (
    SPECIALISTS,
    render_supervisor_prompt,
)
from app.graph.state import SupportState
from app.llm.provider import LLMClient

logger = logging.getLogger(__name__)

__all__ = [
    "RouteNode",
]


def _build_context_summary(retrieved_docs: list[dict[str, Any]] | None) -> str | None:
    """Build a one-line summary of retrieved docs, or None if empty."""
    if not retrieved_docs:
        return None
    sources = []
    for doc in retrieved_docs:
        source = doc.get("source", "unknown")
        section = doc.get("section", "")
        label = f"{source}" + (f" — {section}" if section else "")
        sources.append(label)
    unique = sorted(set(sources))
    return "Found relevant docs: " + "; ".join(unique) if unique else None


def _normalise_specialist(raw: str) -> str | None:
    """Return the specialist name if *raw* matches one of the five; else None."""
    cleaned = raw.strip().strip('"').strip("'").lower()
    for s in SPECIALISTS:
        if cleaned == s:
            return s
    return None


class RouteNode:
    """Graph node that calls the LLM to route to the right specialist agent."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm or LLMClient()

    def __call__(self, state: SupportState) -> dict[str, Any]:
        category = state.get("category")
        retrieved_docs = state.get("retrieved_docs")

        context_summary = _build_context_summary(retrieved_docs)
        prompt = render_supervisor_prompt(
            category=category,
            context_summary=context_summary,
        )

        raw = self._llm.generate(prompt)
        specialist = _normalise_specialist(raw)

        if specialist is None:
            specialist = "general"
            logger.warning(
                "Supervisor returned invalid specialist '%s'; falling back to 'general'",
                raw,
            )

        if context_summary:
            routing_reason = f"Category: {category}, context confirms {specialist} issue"
        else:
            routing_reason = f"Category: {category}"

        return {
            "active_agent": specialist,
            "routing_reason": routing_reason,
        }
