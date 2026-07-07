"""
The shared prompt shell every specialist agent fills in: role
description, account data section, and reference material section.
Keeping this in one place is what lets a new specialist be added
without touching the others.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "render_generic_agent_prompt",
]


def render_generic_agent_prompt(
    *,
    customer_message: str,
    conversation_history: list[dict[str, str]] | None = None,
    retrieved_docs: list[dict[str, Any]] | None = None,
    business_data: dict[str, Any] | None = None,
    role_description: str | None = None,
) -> str:
    """Render a single-turn support agent prompt.

    The *role_description* overrides the default role line when a
    specialist wants a distinct persona (billing, order, etc.).
    The agent is grounded in the retrieved knowledge docs and any
    business data (order / payment records).  If no context is
    available the agent must say so rather than invent answers.
    """
    lines: list[str] = []

    if role_description:
        lines.append(role_description)
    else:
        lines.append("You are a helpful customer support agent.")
    lines.append(
        "Answer the customer's question using only the context provided below."
    )
    lines.append(
        "If the context does not contain the answer, say so — do not make up information."
    )
    lines.append("")

    # ── Conversation history ───────────────────────────────────────────────
    if conversation_history:
        lines.append("## Conversation history")
        for msg in conversation_history:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")
        lines.append("")

    # ── Retrieved knowledge docs ───────────────────────────────────────────
    if retrieved_docs:
        lines.append("## Reference material")
        for i, doc in enumerate(retrieved_docs, 1):
            source = doc.get("source", "unknown")
            section = doc.get("section", "")
            text = doc.get("text", "")
            header = f"{source}" + (f" — {section}" if section else "")
            lines.append(f"[{i}] {header}")
            lines.append(f"    {text}")
        lines.append("")

    # ── Business data ──────────────────────────────────────────────────────
    if business_data:
        lines.append("## Account / order data")
        for key, value in business_data.items():
            lines.append(f"{key}: {value}")
        lines.append("")

    # ── Customer message ───────────────────────────────────────────────────
    lines.append("## Customer message")
    lines.append(customer_message)

    return "\n".join(lines)
