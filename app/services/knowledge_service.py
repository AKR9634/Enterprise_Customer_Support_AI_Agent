"""
search(query_text) — embeds the query, retrieves matching chunks
from Qdrant via the retriever, dedupes/re-ranks them, and assembles
a token-budgeted, citation-formatted context string.
"""
