"""
Node 8 — Confidence + Escalation Decision. Combines intent
confidence with the grounding check (hard-capped if ungrounded) and
decides whether to escalate, calling EscalationService.evaluate().
"""

from __future__ import annotations

from typing import Any

from app import config
from app.graph.state import SupportState
from app.services.escalation_service import EscalationService

__all__ = [
    "DecideNode",
]


class DecideNode:
    """Graph node that makes the final escalation decision.

    **Structural guarantee enforced in code**: when *escalate* is
    True the *final_response* is always the fixed acknowledgment
    message from config, never *draft_response*.
    """

    def __call__(self, state: SupportState) -> dict[str, Any]:
        intent_confidence = state.get("intent_confidence")
        grounding_ok = state.get("grounding_ok", False)
        category = state.get("category")

        # ── Force escalation when no knowledge context was found ──────────
        # Skip for "general" category — greetings and chitchat don't need KB.
        retrieved_docs = state.get("retrieved_docs") or []
        if not retrieved_docs:
            if category == "general":
                escalate = False
                reason = None
                effective_confidence = intent_confidence or 0.95
            else:
                escalate = True
                reason = "No relevant knowledge base context found for this question."
                effective_confidence = None
        else:
            # ── Cap confidence when ungrounded ────────────────────────────
            if grounding_ok:
                effective_confidence = intent_confidence
            else:
                effective_confidence = 0.0

            # ── Evaluate escalation ───────────────────────────────────────
            escalate, reason = EscalationService.evaluate(effective_confidence)

        # ── Assemble outputs ──────────────────────────────────────────────
        result: dict[str, Any] = {
            "confidence": effective_confidence,
            "escalate": escalate,
            "escalation_reason": reason,
        }

        # Persistence (enqueue) happens in the API layer (chat.py),
        # not here — the graph node only makes the decision.

        # ── Structural guarantee: never leak draft_response on escalation ─
        if escalate:
            result["final_response"] = config.ESCALATION_ACKNOWLEDGMENT
        else:
            result["final_response"] = state.get("draft_response")

        return result
