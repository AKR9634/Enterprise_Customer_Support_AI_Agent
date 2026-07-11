"""
Inserts sample escalations into the database for the agent review queue.
Run after seed_db.py or seed_tickets.py.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import get_connection
from app.config import DATABASE_URL


def seed_escalations() -> None:
    conn = get_connection(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, email FROM customers WHERE role = 'agent' LIMIT 1")
            agent = cur.fetchone()
            agent_id = str(agent[0]) if agent else None

            cur.execute("SELECT id, subject, customer_id FROM tickets ORDER BY created_at")
            tickets = cur.fetchall()

        if not tickets:
            print("No tickets found. Run seed_db.py first.")
            return

        escalations = [
            {
                "ticket_id": tickets[0][0],
                "status": "queued",
                "priority": "high",
                "escalation_reason": "Low confidence (0.45) — LLM could not verify tracking status from retrieved order data. Order shows 'shipped' but no delivery scan within expected window.",
                "category": "order",
                "confidence": 0.45,
                "customer_message": "I ordered a Widget Pro last week and it still hasn't arrived. Can you check what's going on?",
                "draft_response": "I can see your order #1001 was marked as shipped on July 5. The tracking number is 1Z999AA10123456784. However, there have been no new scan updates since July 8. I recommend waiting 2 more business days.",
                "routing_reason": "Order specialist — order tracking inquiry",
                "retrieved_docs": '[{"title": "Shipping Policy", "content": "Standard shipping takes 3-5 business days.", "score": 0.91}, {"title": "Order FAQ", "content": "If your order hasn\'t arrived within the estimated window, contact support.", "score": 0.87}]',
                "business_data": '{"order_id": "1001", "status": "shipped", "tracking": "1Z999AA10123456784", "carrier": "UPS", "shipped_date": "2026-07-05", "last_scan": "2026-07-08"}',
            },
            {
                "ticket_id": tickets[1][0],
                "status": "queued",
                "priority": "normal",
                "escalation_reason": "Ungrounded claim detected — LLM stated 'return label will be emailed' but the returns system requires human authorization for high-value items (>$100).",
                "category": "order",
                "confidence": 0.62,
                "customer_message": "I received the wrong item. I ordered a Gadget X but got a Widget Pro instead. I need a replacement.",
                "draft_response": "I apologize for the mix-up. We will send you a return label for the Widget Pro and ship a replacement Gadget X once the return is scanned by the carrier.",
                "routing_reason": "Order specialist — return/replacement request",
                "retrieved_docs": '[{"title": "Return Policy", "content": "Wrong items are replaced at no cost within 30 days.", "score": 0.94}, {"title": "Return Policy", "content": "A prepaid return label is provided for incorrect items.", "score": 0.88}]',
                "business_data": '{"order_id": "1001", "status": "delivered", "items_ordered": ["Gadget X"], "items_delivered": ["Widget Pro"], "order_total": 189.97}',
            },
            {
                "ticket_id": tickets[2][0],
                "status": "in_review",
                "priority": "normal",
                "assigned_reviewer": agent_id,
                "escalation_reason": "Billing inquiry requires manual review — the invoice #1234 shows a double charge, but the payment gateway logs are inconclusive on whether the second charge was captured or just authorized.",
                "category": "billing",
                "confidence": 0.55,
                "customer_message": "Invoice #1234 shows a charge of $49.99 but I was charged twice. Please refund the duplicate.",
                "draft_response": "I see invoice #1234 for $49.99 on your account. Let me check if there is a duplicate charge.",
                "routing_reason": "Billing specialist — duplicate charge review",
                "retrieved_docs": '[{"title": "Billing Policy", "content": "Duplicate charges are refunded within 5-7 business days.", "score": 0.92}]',
                "business_data": '{"invoice_id": "1234", "amount": 49.99, "status": "paid", "payment_attempts": 2, "captured": 1, "authorized": 2}',
            },
            {
                "ticket_id": tickets[3][0],
                "status": "resolved",
                "priority": "low",
                "assigned_reviewer": agent_id,
                "escalation_reason": "Agent assignment test — ticket from an agent account processed through escalation for dashboard testing.",
                "category": "general",
                "confidence": 0.88,
                "customer_message": "This is a test ticket for the agent dashboard.",
                "draft_response": "This is a test response for dashboard review purposes.",
                "routing_reason": "General specialist — test ticket",
                "retrieved_docs": "[]",
                "business_data": "{}",
            },
            {
                "ticket_id": tickets[4][0],
                "status": "in_review",
                "priority": "urgent",
                "assigned_reviewer": agent_id,
                "escalation_reason": "Urgent billing dispute — customer claims an unauthorized charge of $199.99. Confidence is high but policy requires human sign-off for fraud-related escalations.",
                "category": "billing",
                "confidence": 0.81,
                "customer_message": "I see a charge for $199.99 on my account that I didn't authorize. This needs to be reversed immediately.",
                "draft_response": "I understand your concern about the unauthorized charge of $199.99. I have flagged this for our billing team who will investigate and process a reversal.",
                "routing_reason": "Billing specialist — unauthorized charge / potential fraud",
                "retrieved_docs": '[{"title": "Fraud Policy", "content": "Unauthorized charges must be reviewed by a human agent before reversal.", "score": 0.96}, {"title": "Billing Policy", "content": "Disputed charges are investigated within 10 business days.", "score": 0.89}]',
                "business_data": '{"invoice_id": "5678", "amount": 199.99, "status": "pending", "payment_method": "Visa ****4242", "customer_noted": "unauthorized"}',
            },
            {
                "ticket_id": tickets[5][0],
                "status": "queued",
                "priority": "high",
                "escalation_reason": "Low confidence (0.38) on account access issue — LLM could not verify identity because the customer's email is unverified and recent login location differs from registered address.",
                "category": "account",
                "confidence": 0.38,
                "customer_message": "I can't log into my account. It says my password is wrong but I'm sure I'm typing it correctly. Can you help me reset it?",
                "draft_response": "I can help with a password reset. I'll send a reset link to your registered email address.",
                "routing_reason": "Account specialist — access recovery with low identity confidence",
                "retrieved_docs": '[{"title": "Account Security FAQ", "content": "Password resets require verified email. If email is unverified, contact support for manual verification.", "score": 0.93}, {"title": "Account Security FAQ", "content": "Unusual login locations may trigger additional verification.", "score": 0.85}]',
                "business_data": '{"email_verified": false, "two_factor_enabled": false, "account_locked": false, "last_login": "2026-07-10T23:15:00Z", "last_login_ip": "203.0.113.45", "registered_ip": "198.51.100.22"}',
            },
        ]

        now = datetime.now(timezone.utc)
        with conn.cursor() as cur:
            for idx, e in enumerate(escalations):
                params = {**e, "created_at": now, "updated_at": now}
                params.setdefault("assigned_reviewer", None)
                cur.execute(
                    """
                    INSERT INTO escalations (
                        ticket_id, status, priority, assigned_reviewer,
                        escalation_reason, category, confidence,
                        customer_message, draft_response, routing_reason,
                        retrieved_docs, business_data, created_at, updated_at
                    ) VALUES (
                        %(ticket_id)s, %(status)s, %(priority)s, %(assigned_reviewer)s,
                        %(escalation_reason)s, %(category)s, %(confidence)s,
                        %(customer_message)s, %(draft_response)s, %(routing_reason)s,
                        %(retrieved_docs)s::jsonb, %(business_data)s::jsonb,
                        %(created_at)s, %(updated_at)s
                    )
                    ON CONFLICT DO NOTHING
                    """,
                    params,
                )
                print(f"  [{e['status']:>10}] {e['priority']:>6}  {e['category']:>7} — {e['escalation_reason'][:60]}...")

        conn.commit()
        print(f"\nSeeded {len(escalations)} escalations.")

    finally:
        conn.close()


if __name__ == "__main__":
    seed_escalations()
