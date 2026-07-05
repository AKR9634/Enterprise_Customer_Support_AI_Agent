"""
Integration tests for the ingestion pipeline against a real Qdrant Cloud
collection. Tests are skipped if QDRANT_URL is not set.

A throwaway test collection is used and cleaned up after each test run.

These tests pass ``collection_name`` directly to ``run_ingestion`` rather
than relying on environment-variable overrides, because ``ingest.py``
imports ``QDRANT_COLLECTION`` from ``app.config`` at module level and
reloading the config module does not retroactively update the cached
import in ``ingest.py``.
"""

import os

import pytest
from qdrant_client import QdrantClient

from app.config import QDRANT_API_KEY, QDRANT_URL
from app.rag.ingest import _get_qdrant_client, run_ingestion

pytestmark = pytest.mark.skipif(
    not QDRANT_URL,
    reason="QDRANT_URL not set — skipping real Qdrant test",
)


@pytest.fixture
def test_collection() -> str:
    """Return a unique test collection name and clean it up after."""
    import uuid
    name = f"test_ingestion_{uuid.uuid4().hex[:8]}"
    yield name
    client = _get_qdrant_client()
    try:
        client.delete_collection(name)
    except Exception:
        pass


class TestIngestionAgainstRealQdrant:

    def test_run_ingestion_on_docs(self, test_collection: str) -> None:
        """Load docs from the project's docs/, ingest into test collection."""
        docs_dir = os.path.join(os.path.dirname(__file__), "..", "..", "docs")
        result = run_ingestion(docs_dir, collection_name=test_collection)

        assert result["total_docs"] == 3, "Should find 3 .md files in docs/"
        assert result["total_chunks"] > 0, "Should produce at least one chunk"
        assert result["upserted_points"] == result["total_chunks"]

    def test_idempotency_point_count_unchanged(self, test_collection: str) -> None:
        """Running ingestion twice must not increase the point count."""
        docs_dir = os.path.join(os.path.dirname(__file__), "..", "..", "docs")

        run1 = run_ingestion(docs_dir, collection_name=test_collection)
        run2 = run_ingestion(docs_dir, collection_name=test_collection)

        assert run1["upserted_points"] == run2["upserted_points"]

        # Also verify directly via Qdrant API
        client = _get_qdrant_client()
        count_before = client.count(test_collection)
        run_ingestion(docs_dir, collection_name=test_collection)
        count_after = client.count(test_collection)
        assert count_after.count == count_before.count, (
            f"Point count changed from {count_before.count} to {count_after.count}"
        )

    def test_chunk_metadata(self, test_collection: str) -> None:
        """Verify that upserted chunks have correct metadata."""
        docs_dir = os.path.join(os.path.dirname(__file__), "..", "..", "docs")
        run_ingestion(docs_dir, collection_name=test_collection)

        client = _get_qdrant_client()
        scroll_result = client.scroll(
            collection_name=test_collection,
            limit=100,
            with_payload=True,
            with_vectors=False,
        )
        points = scroll_result[0]

        assert len(points) > 0
        for pt in points:
            payload = pt.payload or {}
            assert "source" in payload, "Missing 'source' in metadata"
            assert "section" in payload, "Missing 'section' in metadata"
            assert "chunk_index" in payload, "Missing 'chunk_index' in metadata"
            assert "text" in payload, "Missing 'text' in metadata"
            assert isinstance(payload["source"], str)
            assert isinstance(payload["section"], str)
            assert isinstance(payload["chunk_index"], int)
            assert isinstance(payload["text"], str)

    def test_vector_dimensions(self, test_collection: str) -> None:
        """All vectors should have dimension 384."""
        docs_dir = os.path.join(os.path.dirname(__file__), "..", "..", "docs")
        run_ingestion(docs_dir, collection_name=test_collection)

        client = _get_qdrant_client()
        scroll_result = client.scroll(
            collection_name=test_collection,
            limit=5,
            with_payload=False,
            with_vectors=True,
        )
        points = scroll_result[0]

        assert len(points) > 0
        for pt in points:
            assert len(pt.vector) == 384, f"Expected 384-dim vector, got {len(pt.vector)}"
