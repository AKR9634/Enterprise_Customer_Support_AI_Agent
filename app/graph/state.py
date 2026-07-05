"""
SupportState TypedDict — the single object threaded through every
graph node. Each node reads the fields it needs and writes the
fields it produces; LangGraph merges partial updates as it runs.
"""
