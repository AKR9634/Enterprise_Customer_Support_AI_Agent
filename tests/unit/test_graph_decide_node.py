"""Unit tests for DecideNode.

Verifies:
- Confident + grounded -> final_response == draft_response, escalate == False
- Low confidence -> escalate == True, final_response != draft_response
- Ungrounded -> escalate == True, final_response != draft_response
- Regression: the structural guarantee (draft_response is never leaked when escalate is True)
"""

from unittest.mock import patch

import pytest

from app.graph.nodes.decide import DecideNode


def _state(**overrides) -> dict:
    base = {
        "intent_confidence": 0.95,
        "grounding_ok": True,
        "draft_response": "Here is your answer.",
    }
    base.update(overrides)
    return base


class TestDecideNode:

    def test_confident_and_grounded_returns_draft(self) -> None:
        node = DecideNode()
        result = node(_state(intent_confidence=0.95, grounding_ok=True))

        assert result["escalate"] is False
        assert result["final_response"] == "Here is your answer."
        assert result["confidence"] == 0.95

    def test_low_confidence_escalates(self) -> None:
        node = DecideNode()
        result = node(_state(intent_confidence=0.3, grounding_ok=True))

        assert result["escalate"] is True
        assert result["escalation_reason"] is not None
        assert result["final_response"] != "Here is your answer."
        assert result["confidence"] == 0.3

    def test_ungrounded_escalates_even_with_high_confidence(self) -> None:
        node = DecideNode()
        result = node(_state(intent_confidence=0.95, grounding_ok=False))

        assert result["escalate"] is True
        assert result["escalation_reason"] is not None
        assert result["confidence"] == 0.0  # capped
        assert result["final_response"] != "Here is your answer."

    def test_structural_guarantee_never_leaks_draft_on_escalation(self) -> None:
        """Regression test: when escalate is True, final_response must
        never equal draft_response.  This enforces the code-level
        structural guarantee."""
        node = DecideNode()

        scenarios = [
            {"intent_confidence": 0.1, "grounding_ok": True},
            {"intent_confidence": 0.95, "grounding_ok": False},
            {"intent_confidence": 0.0, "grounding_ok": False},
            {"intent_confidence": None, "grounding_ok": True},
        ]

        for scenario in scenarios:
            result = node(_state(**scenario))
            if result["escalate"]:
                assert (
                    result["final_response"] != "Here is your answer."
                ), (
                    f"Escalation leaked draft_response "
                    f"(scenario: {scenario})"
                )
            else:
                assert result["final_response"] == "Here is your answer."

    def test_none_confidence_escalates(self) -> None:
        node = DecideNode()
        result = node(_state(intent_confidence=None, grounding_ok=True))

        assert result["escalate"] is True
        assert result["confidence"] is None
        assert result["final_response"] != "Here is your answer."

    def test_only_writes_own_fields(self) -> None:
        node = DecideNode()
        result = node(_state())

        assert set(result.keys()) == {
            "confidence",
            "escalate",
            "escalation_reason",
            "final_response",
        }
