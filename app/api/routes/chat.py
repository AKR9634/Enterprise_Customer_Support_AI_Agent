"""
POST /chat/messages — the single entry point into the AI pipeline.
Persists the inbound message, invokes the LangGraph workflow, then
persists and returns the assistant's final (verified or escalated) reply.
"""
