"""
evaluate() decides whether a chat turn should escalate (confidence
or grounding failure); enqueue(), claim(), and resolve() manage an
escalation through its lifecycle in the human review queue.
"""

from __future__ import annotations

from app import config

__all__ = [
    "EscalationService",
]


class EscalationService:
    """Deterministic escalation evaluation and lifecycle management."""

    @staticmethod
    def evaluate(
        confidence: float | None,
        *,
        threshold: float | None = None,
    ) -> tuple[bool, str | None]:
        """Return (escalate, reason) based on confidence vs threshold.

        A confidence of *None* or below the threshold triggers escalation.
        """
        threshold = threshold if threshold is not None else config.CONFIDENCE_THRESHOLD

        if confidence is None:
            return True, "No confidence score available"

        if confidence < threshold:
            return True, (
                f"Confidence {confidence:.2f} is below threshold {threshold:.2f}"
            )

        return False, None

    # ── Lifecycle stubs (Phase 5) ──────────────────────────────────────────

    def enqueue(self, escalation_id: str) -> None:
        """Add an escalation to the human review queue."""

    def claim(self, escalation_id: str, agent_id: str) -> None:
        """Assign an escalation to a human agent."""

    def resolve(self, escalation_id: str) -> None:
        """Mark an escalation as resolved."""
