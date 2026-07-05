"""
FastAPI dependency wiring: builds a DB connection, then constructs
each repository and service from it, so routes just declare
Depends(get_ticket_service) instead of wiring this by hand.
"""
