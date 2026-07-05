"""
Loads a document, splits it into heading-aware chunks, embeds each
chunk, and upserts it into Qdrant using a deterministic point ID so
re-running ingestion on an edited doc updates rather than duplicates.
"""
