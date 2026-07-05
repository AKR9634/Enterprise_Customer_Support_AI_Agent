"""
Node 8 — Confidence + Escalation Decision. Combines intent
confidence with the grounding check (hard-capped if ungrounded) and
decides whether to escalate, calling EscalationService.evaluate().
"""
