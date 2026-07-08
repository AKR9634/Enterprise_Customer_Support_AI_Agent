from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.repositories.escalation_repository import Escalation
from app.services.escalation_service import EscalationConflictError, EscalationService


def _make_escalation(
    status: str = "queued",
    assigned_reviewer=None,
) -> Escalation:
    return Escalation(
        id=uuid4(),
        ticket_id=uuid4(),
        status=status,
        priority="normal",
        assigned_reviewer=assigned_reviewer,
        escalation_reason="Low confidence",
        category="general",
        confidence=0.3,
        customer_message="Help me",
        draft_response="Sorry I cannot help",
        routing_reason="general",
        retrieved_docs=[],
        business_data={},
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


class TestEscalationServiceEnqueue:

    def test_creates_escalation_and_transitions_ticket(self) -> None:
        escalation = _make_escalation()
        mock_conn = MagicMock()

        with (
            patch(
                "app.services.escalation_service.EscalationRepository.create",
                return_value=escalation,
            ) as mock_create,
            patch(
                "app.services.escalation_service.TicketService.transition_status",
            ) as mock_transition,
        ):
            result = EscalationService().enqueue(
                mock_conn,
                ticket_id=str(escalation.ticket_id),
                escalation_reason=escalation.escalation_reason,
                category=escalation.category,
                confidence=escalation.confidence,
                customer_message=escalation.customer_message,
                draft_response=escalation.draft_response,
                routing_reason=escalation.routing_reason,
                retrieved_docs=escalation.retrieved_docs,
                business_data=escalation.business_data,
            )

        mock_create.assert_called_once()
        mock_transition.assert_called_once_with(
            mock_conn, str(escalation.ticket_id), "escalated"
        )
        assert result == escalation


class TestEscalationServiceClaim:

    def test_claims_escalation_and_transitions_ticket(self) -> None:
        escalation = _make_escalation()
        agent_id = str(uuid4())
        mock_conn = MagicMock()

        with (
            patch(
                "app.services.escalation_service.EscalationRepository.claim_atomic",
                return_value=escalation,
            ) as mock_claim,
            patch(
                "app.services.escalation_service.TicketService.transition_status",
            ) as mock_transition,
        ):
            result = EscalationService().claim(
                mock_conn,
                str(escalation.id),
                agent_id,
            )

        mock_claim.assert_called_once_with(mock_conn, str(escalation.id), agent_id)
        mock_transition.assert_called_once_with(
            mock_conn, str(escalation.ticket_id), "pending"
        )
        assert result == escalation

    def test_raises_conflict_when_already_claimed(self) -> None:
        escalation_id = str(uuid4())
        agent_id = str(uuid4())
        mock_conn = MagicMock()

        with patch(
            "app.services.escalation_service.EscalationRepository.claim_atomic",
            return_value=None,
        ):
            with pytest.raises(EscalationConflictError) as exc:
                EscalationService().claim(mock_conn, escalation_id, agent_id)

        assert escalation_id in str(exc.value)
        assert agent_id in str(exc.value)

    def test_concurrent_claims_only_one_succeeds(self) -> None:
        escalation = _make_escalation()
        escalation_id = str(escalation.id)
        agent_a = str(uuid4())
        agent_b = str(uuid4())
        mock_conn = MagicMock()

        def claim_side_effect(conn, eid, aid):
            if aid == agent_a:
                return escalation
            return None

        with (
            patch(
                "app.services.escalation_service.EscalationRepository.claim_atomic",
                side_effect=claim_side_effect,
            ),
            patch(
                "app.services.escalation_service.TicketService.transition_status",
            ),
        ):
            result_a = EscalationService().claim(mock_conn, escalation_id, agent_a)
            assert result_a is not None

            with pytest.raises(EscalationConflictError):
                EscalationService().claim(mock_conn, escalation_id, agent_b)


class TestEscalationServiceResolve:

    def test_resolves_escalation_and_transitions_ticket(self) -> None:
        escalation = _make_escalation(status="in_review", assigned_reviewer=uuid4())
        resolved = _make_escalation(
            status="resolved",
            assigned_reviewer=escalation.assigned_reviewer,
        )
        mock_conn = MagicMock()

        with (
            patch(
                "app.services.escalation_service.EscalationRepository.update_status",
                return_value=resolved,
            ) as mock_update,
            patch(
                "app.services.escalation_service.TicketService.transition_status",
            ) as mock_transition,
        ):
            result = EscalationService().resolve(
                mock_conn,
                str(escalation.id),
            )

        mock_update.assert_called_once_with(
            mock_conn, str(escalation.id), "resolved"
        )
        mock_transition.assert_called_once_with(
            mock_conn, str(resolved.ticket_id), "resolved"
        )
        assert result.status == "resolved"

    def test_raises_value_error_when_escalation_not_found(self) -> None:
        mock_conn = MagicMock()

        with patch(
            "app.services.escalation_service.EscalationRepository.update_status",
            return_value=None,
        ):
            with pytest.raises(ValueError, match="not found"):
                EscalationService().resolve(mock_conn, str(uuid4()))
