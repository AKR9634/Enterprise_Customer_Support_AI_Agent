"""
Node 7 — Response Verification. A separate LLM call that checks
whether every factual claim in draft_response traces back to
retrieved_docs or business_data, writing grounding_ok.
"""

from __future__ import annotations

from typing import Any

from app.graph.state import SupportState
from app.llm.provider import LLMClient

__all__ = [
    "VerifyNode",
]

_VERIFICATION_SYSTEM_PROMPT = (
    "You are a strict fact-checker. Your job is to determine whether "
    "every factual claim in the draft response is supported by the "
    "provided reference material or business data."
)

_VERIFICATION_USER_TEMPLATE = """\
## Draft response
{draft}

## Reference material
{references}

## Business data
{business_data}

Is every factual claim in the draft response supported by the reference \
material or business data?  Answer only "YES" or "NO"."""


class VerifyNode:
    """Graph node that verifies the draft response is grounded in the
    retrieved knowledge and business data."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm or LLMClient()

    def __call__(self, state: SupportState) -> dict[str, Any]:
        draft = state.get("draft_response", "")
        if not draft:
            return {"grounding_ok": False}

        retrieved_docs = state.get("retrieved_docs") or []
        business_data = state.get("business_data") or {}

        references = _format_references(retrieved_docs)
        business_str = _format_business_data(business_data)

        prompt = _VERIFICATION_USER_TEMPLATE.format(
            draft=draft,
            references=references or "(none)",
            business_data=business_str or "(none)",
        )

        answer = self._llm.generate(
            prompt,
            system_prompt=_VERIFICATION_SYSTEM_PROMPT,
        )

        return {"grounding_ok": answer.strip().upper().startswith("YES")}


def _format_references(docs: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for i, doc in enumerate(docs, 1):
        source = doc.get("source", "unknown")
        text = doc.get("text", "")
        lines.append(f"[{i}] {source}")
        lines.append(f"    {text}")
    return "\n".join(lines)


def _format_business_data(data: dict[str, Any]) -> str:
    if not data:
        return ""
    return "\n".join(f"{k}: {v}" for k, v in data.items())
