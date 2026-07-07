"""
The Supervisor's prompt template — intentionally narrow. Takes only
the category and short summaries, never the full conversation, so
routing stays a simple classification task.

Specialist options: billing, order, account, product, general.
"""

from __future__ import annotations

__all__ = [
    "render_supervisor_prompt",
]

SPECIALISTS = ["billing", "order", "account", "product", "general"]


def render_supervisor_prompt(
    *,
    category: str | None,
    context_summary: str | None = None,
) -> str:
    """Render the Supervisor routing prompt.

    The LLM is asked to pick exactly one specialist from the
    predefined list based on the category and an optional one-line
    summary of retrieved knowledge docs.
    """
    lines = [
        "You are a routing supervisor for a customer support system.",
        "Your job is to choose which specialist should handle the customer's request.",
        "",
        f"Classification category: {category or 'unknown'}",
    ]

    if context_summary:
        lines.append(f"Context summary: {context_summary}")

    lines.append("")
    lines.append(
        f"Respond with exactly one word from the following list: "
        f"{', '.join(SPECIALISTS)}."
    )
    lines.append("Do not include any explanation or additional text.")

    return "\n".join(lines)
