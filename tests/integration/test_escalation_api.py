"""Integration tests for agent-facing escalation API endpoints."""

import uuid

import pytest
from fastapi.testclient import TestClient


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class TestListEscalations:
    def test_returns_queued_escalations(self, client: TestClient, agent_token: str, seed_ticket_and_escalation):
        resp = client.get("/escalations", headers=_auth_header(agent_token))
        assert resp.status_code == 200
        body = resp.json()
        assert "escalations" in body
        assert len(body["escalations"]) >= 1

    def test_returns_403_for_customer(self, client: TestClient, customer_token: str):
        resp = client.get("/escalations", headers=_auth_header(customer_token))
        assert resp.status_code == 403


class TestEscalationContext:
    def test_returns_context(self, client: TestClient, agent_token: str, seed_ticket_and_escalation):
        escalation_id = str(seed_ticket_and_escalation["escalation"].id)
        resp = client.get(f"/escalations/{escalation_id}/context", headers=_auth_header(agent_token))
        assert resp.status_code == 200
        body = resp.json()
        assert body["escalation_id"] == escalation_id
        assert body["escalation_reason"] == "Low confidence"
        assert body["draft_response"] == "Test draft"
        assert body["routing_reason"] == "routed to general"
        assert body["confidence"] == 0.3
        assert len(body["retrieved_docs"]) == 1
        assert body["business_data"]["key"] == "value"

    def test_404_for_unknown_id(self, client: TestClient, agent_token: str):
        resp = client.get(f"/escalations/{uuid.uuid4()}/context", headers=_auth_header(agent_token))
        assert resp.status_code == 404

    def test_returns_403_for_customer(self, client: TestClient, customer_token: str, seed_ticket_and_escalation):
        escalation_id = str(seed_ticket_and_escalation["escalation"].id)
        resp = client.get(f"/escalations/{escalation_id}/context", headers=_auth_header(customer_token))
        assert resp.status_code == 403


class TestClaimEscalation:
    def test_claim_succeeds(self, client: TestClient, agent_token: str, seed_ticket_and_escalation):
        escalation_id = str(seed_ticket_and_escalation["escalation"].id)
        resp = client.post(f"/escalations/{escalation_id}/claim", headers=_auth_header(agent_token))
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "in_review"
        assert body["assigned_reviewer"] is not None

    def test_claim_conflict_returns_409(self, client: TestClient, agent_token: str, second_agent_token: str, seed_ticket_and_escalation):
        escalation_id = str(seed_ticket_and_escalation["escalation"].id)

        resp1 = client.post(f"/escalations/{escalation_id}/claim", headers=_auth_header(agent_token))
        assert resp1.status_code == 200

        resp2 = client.post(f"/escalations/{escalation_id}/claim", headers=_auth_header(second_agent_token))
        assert resp2.status_code == 409

    def test_returns_403_for_customer(self, client: TestClient, customer_token: str, seed_ticket_and_escalation):
        escalation_id = str(seed_ticket_and_escalation["escalation"].id)
        resp = client.post(f"/escalations/{escalation_id}/claim", headers=_auth_header(customer_token))
        assert resp.status_code == 403


class TestResolveEscalation:
    def test_resolve_succeeds(self, client: TestClient, agent_token: str, seed_ticket_and_escalation):
        escalation = seed_ticket_and_escalation["escalation"]
        ticket_id = str(escalation.ticket_id)

        claim_resp = client.post(f"/escalations/{escalation.id}/claim", headers=_auth_header(agent_token))
        assert claim_resp.status_code == 200

        resp = client.post(f"/escalations/{escalation.id}/resolve", headers=_auth_header(agent_token))
        assert resp.status_code == 200
        assert resp.json()["status"] == "resolved"

        ticket_resp = client.get(f"/tickets/{ticket_id}", headers=_auth_header(agent_token))
        assert ticket_resp.status_code == 200
        assert ticket_resp.json()["ticket"]["status"] == "resolved"

    def test_404_for_unknown_id(self, client: TestClient, agent_token: str):
        resp = client.post(f"/escalations/{uuid.uuid4()}/resolve", headers=_auth_header(agent_token))
        assert resp.status_code == 404

    def test_returns_403_for_customer(self, client: TestClient, customer_token: str, seed_ticket_and_escalation):
        escalation_id = str(seed_ticket_and_escalation["escalation"].id)
        resp = client.post(f"/escalations/{escalation_id}/resolve", headers=_auth_header(customer_token))
        assert resp.status_code == 403



