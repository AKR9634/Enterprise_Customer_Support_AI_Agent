"""
Business rules for tickets: create_ticket, transition_status
(enforces the open -> pending -> resolved/escalated -> closed state
machine), and set_priority. The only place ticket rules are allowed
to live.
"""
