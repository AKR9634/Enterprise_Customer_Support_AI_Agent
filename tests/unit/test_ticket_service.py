from datetime import datetime
from uuid import uuid4

import pytest
from unittest.mock import MagicMock, patch

from app.repositories.ticket_repository import Ticket
from app.services.ticket_service import InvalidTicketTransition, TicketService

_ALL_STATUSES = ["open", "pending", "resolved", "escalated", "closed"]

_LEGAL: dict[str, set[str]] = {
    "open": {"pending"},
    "pending": {"resolved", "escalated"},
    "resolved": {"closed"},
    "escalated": {"closed"},
    "closed": set(),
}

_ILLEGAL_PAIRS: list[tuple[str, str]] = []
for current in _ALL_STATUSES:
    for new in _ALL_STATUSES:
        if current == new:
            continue
        if new not in _LEGAL.get(current, set()):
            _ILLEGAL_PAIRS.append((current, new))


def _make_ticket(status: str) -> Ticket:
    return Ticket(
        id=uuid4(),
        customer_id=uuid4(),
        subject="Test ticket",
        status=status,
        priority="normal",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


class TestTicketServiceTransitionStatus:

    @pytest.mark.parametrize("current,new", [
        ("open", "pending"),
        ("pending", "resolved"),
        ("pending", "escalated"),
        ("resolved", "closed"),
        ("escalated", "closed"),
    ])
    def test_legal_transitions(self, current: str, new: str) -> None:
        ticket = _make_ticket(current)
        updated = _make_ticket(new)

        with (
            patch("app.services.ticket_service.TicketRepository.get_by_id", return_value=ticket) as mock_get,
            patch("app.services.ticket_service.TicketRepository.update_status", return_value=updated) as mock_update,
        ):
            result = TicketService.transition_status(MagicMock(), ticket.id, new)

        mock_get.assert_called_once()
        mock_update.assert_called_once()
        assert result.status == new

    @pytest.mark.parametrize("current,new", _ILLEGAL_PAIRS)
    def test_illegal_transitions(self, current: str, new: str) -> None:
        ticket = _make_ticket(current)

        with patch("app.services.ticket_service.TicketRepository.get_by_id", return_value=ticket):
            with pytest.raises(InvalidTicketTransition) as exc:
                TicketService.transition_status(MagicMock(), ticket.id, new)

        assert str(ticket.id) in str(exc.value)
        assert current in str(exc.value)
        assert new in str(exc.value)

    def test_ticket_not_found(self) -> None:
        with patch("app.services.ticket_service.TicketRepository.get_by_id", return_value=None):
            with pytest.raises(ValueError, match="not found"):
                TicketService.transition_status(MagicMock(), uuid4(), "pending")


class TestTicketServiceCreateTicket:

    def test_create_ticket_delegates_to_repo(self) -> None:
        expected = _make_ticket("open")

        with patch("app.services.ticket_service.TicketRepository.create", return_value=expected) as mock_create:
            result = TicketService.create_ticket(MagicMock(), expected.customer_id, "Test", "high")

        mock_create.assert_called_once()
        assert result == expected
