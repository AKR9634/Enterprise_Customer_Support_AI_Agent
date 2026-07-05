"""
Unit tests for the ingestion pipeline.

Mock QdrantClient and SentenceTransformer so no network or model
download is required. Tests focus on chunking logic, point ID
determinism, and orchestration correctness.
"""

import hashlib
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from app.rag.ingest import (
    _chunk_documents,
    _chunk_text_by_paragraphs,
    _load_docs,
    _make_point_id,
    _parse_sections,
    _section_to_chunks,
    _upsert_chunks,
    run_ingestion,
)


# ── Helper factories ──────────────────────────────────────────────────────────

def _fake_embed_batch(texts: list[str]) -> list[list[float]]:
    """Return a fixed 384-dim vector per text (all zeros)."""
    return [[0.0] * 384 for _ in texts]


# ── _parse_sections ───────────────────────────────────────────────────────────

class TestParseSections:

    def test_empty_content(self) -> None:
        assert _parse_sections("") == []

    def test_only_whitespace(self) -> None:
        assert _parse_sections("  \n\n  ") == []

    def test_no_headings(self) -> None:
        result = _parse_sections("just plain text\nwithout any headings")
        assert len(result) == 1
        assert result[0]["heading"] == ""
        assert "just plain text" in result[0]["text"]
        assert "headings" in result[0]["text"]

    def test_multiple_headings(self) -> None:
        content = """## Shipping
Standard: 5-8 days
## Returns
Within 30 days
## Support
Email us"""
        result = _parse_sections(content)
        assert len(result) == 3
        assert result[0]["heading"] == "Shipping"
        assert result[1]["heading"] == "Returns"
        assert result[2]["heading"] == "Support"

    def test_heading_with_content(self) -> None:
        content = "## Pricing\n$19/month for Basic"
        result = _parse_sections(content)
        assert len(result) == 1
        assert result[0]["heading"] == "Pricing"
        assert "## Pricing" in result[0]["text"]
        assert "$19/month" in result[0]["text"]

    def test_only_level1_headings(self) -> None:
        """Only ## (level-2) are treated as section boundaries."""
        content = "# Title\nparagraph\n# Another\nmore text"
        result = _parse_sections(content)
        assert len(result) == 1  # whole doc is one section with no heading


# ── _section_to_chunks / _chunk_text_by_paragraphs ────────────────────────────

class TestSectionToChunks:

    def test_small_section_single_chunk(self) -> None:
        section = {"heading": "FAQ", "text": "## FAQ\nShort content."}
        chunks = _section_to_chunks(section, "faq.md", 500, 50, 0)
        assert len(chunks) == 1
        assert chunks[0]["source"] == "faq.md"
        assert chunks[0]["section"] == "FAQ"
        assert chunks[0]["chunk_index"] == 0

    def test_empty_section_returns_empty(self) -> None:
        section = {"heading": "Empty", "text": ""}
        assert _section_to_chunks(section, "doc.md", 500, 50, 0) == []


class TestChunkTextByParagraphs:

    def test_single_paragraph_no_split(self) -> None:
        text = "This is a single paragraph that is short."
        chunks = _chunk_text_by_paragraphs(text, "Test", 500, 50, 0)
        assert len(chunks) == 1
        assert chunks[0]["text"] == text
        assert chunks[0]["chunk_index"] == 0

    def test_multiple_paragraphs_within_limit(self) -> None:
        text = "Para one.\n\nPara two.\n\nPara three."
        chunks = _chunk_text_by_paragraphs(text, "Test", 500, 50, 0)
        assert len(chunks) == 1  # all three fit within 500 chars

    def test_split_into_multiple_chunks(self) -> None:
        # Each "paragraph" is ~100 chars, chunk_size=150 → should split
        paras = "\n\n".join(["A" * 100] * 5)
        chunks = _chunk_text_by_paragraphs(paras, "Test", 150, 20, 0)
        assert len(chunks) >= 2

    def test_overlap_carried(self) -> None:
        text = "A" * 100 + "\n\n" + "B" * 100 + "\n\n" + "C" * 100
        chunks = _chunk_text_by_paragraphs(text, "Test", 130, 30, 0)
        assert len(chunks) >= 2
        # The second chunk should contain overlap from the first chunk's tail
        if len(chunks) >= 2:
            assert "A" in chunks[1]["text"] or len(chunks[1]["text"]) > 100


# ── _chunk_documents ──────────────────────────────────────────────────────────

class TestChunkDocuments:

    def test_single_doc_single_section(self) -> None:
        docs = [{"source": "test.md", "content": "# Title\n## FAQ\nShort."}]
        chunks = _chunk_documents(docs, 500, 50)
        assert len(chunks) == 1
        assert chunks[0]["source"] == "test.md"
        assert chunks[0]["section"] == "FAQ"

    def test_multiple_docs_sequential_indexes(self) -> None:
        docs = [
            {"source": "a.md", "content": "## A\nContent a"},
            {"source": "b.md", "content": "## B\nContent b"},
        ]
        chunks = _chunk_documents(docs, 500, 50)
        assert len(chunks) == 2
        indices = [c["chunk_index"] for c in chunks]
        assert indices == [0, 1]

    def test_large_doc_split_across_sections(self) -> None:
        """Sections that exceed chunk_size get sub-split."""
        # Each paragraph is ~100 chars; 7 paragraphs = ~700 chars > 200 chunk_size
        paras = "\n\n".join(["A" * 100] * 7)
        content = "# Title\n## Long Section\n" + paras
        docs = [{"source": "long.md", "content": content}]
        chunks = _chunk_documents(docs, 200, 20)
        assert len(chunks) >= 2
        for c in chunks:
            assert len(c["text"]) <= 200


# ── _make_point_id ────────────────────────────────────────────────────────────

class TestMakePointID:

    def test_deterministic(self) -> None:
        a = _make_point_id("doc.md", 3)
        b = _make_point_id("doc.md", 3)
        assert a == b

    def test_different_index_different_id(self) -> None:
        a = _make_point_id("doc.md", 0)
        b = _make_point_id("doc.md", 1)
        assert a != b

    def test_different_source_different_id(self) -> None:
        a = _make_point_id("faq.md", 0)
        b = _make_point_id("billing.md", 0)
        assert a != b

    def test_is_md5_hexdigest(self) -> None:
        raw = "faq.md::0"
        expected = hashlib.md5(raw.encode()).hexdigest()
        assert _make_point_id("faq.md", 0) == expected


# ── _load_docs ────────────────────────────────────────────────────────────────

class TestLoadDocs:

    def test_loads_md_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            for name in ("a.md", "b.md", "c.txt"):
                path = os.path.join(tmpdir, name)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(f"content of {name}")
            result = _load_docs(tmpdir)
            sources = {d["source"] for d in result}
            assert sources == {"a.md", "b.md"}  # .txt excluded

    def test_empty_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            assert _load_docs(tmpdir) == []

    def test_nonexistent_dir(self) -> None:
        assert _load_docs("/nonexistent/path") == []


# ── _upsert_chunks (mocked Qdrant) ────────────────────────────────────────────

class TestUpsertChunks:

    @patch("app.rag.ingest._get_qdrant_client")
    def test_upsert_returns_point_count(self, mock_get_client: MagicMock) -> None:
        fake_client = MagicMock()
        fake_client.get_collections.return_value.collections = []
        mock_get_client.return_value = fake_client

        chunks = [
            {"source": "a.md", "section": "FAQ", "chunk_index": 0, "text": "Hello"},
            {"source": "a.md", "section": "FAQ", "chunk_index": 1, "text": "World"},
        ]
        embeddings = [[0.1] * 384, [0.2] * 384]
        count = _upsert_chunks(chunks, embeddings)
        assert count == 2
        fake_client.create_collection.assert_called_once()
        fake_client.upsert.assert_called_once()

    @patch("app.rag.ingest._get_qdrant_client")
    def test_empty_chunks_no_upsert(self, mock_get_client: MagicMock) -> None:
        fake_client = MagicMock()
        mock_get_client.return_value = fake_client
        assert _upsert_chunks([], []) == 0
        fake_client.upsert.assert_not_called()


# ── run_ingestion (orchestrator, fully mocked) ────────────────────────────────

class TestRunIngestion:

    @patch("app.rag.ingest._get_qdrant_client")
    @patch("app.rag.ingest.embed_batch", side_effect=_fake_embed_batch)
    def test_happy_path(
        self,
        mock_embed: MagicMock,
        mock_get_client: MagicMock,
    ) -> None:
        fake_client = MagicMock()
        fake_client.get_collections.return_value.collections = []
        mock_get_client.return_value = fake_client

        with tempfile.TemporaryDirectory() as tmpdir:
            doc_path = os.path.join(tmpdir, "test.md")
            with open(doc_path, "w", encoding="utf-8") as f:
                f.write("# Title\n## Section One\nContent here.\n## Section Two\nMore content.\n")

            result = run_ingestion(tmpdir)

        assert result["total_docs"] == 1
        assert result["total_chunks"] == 2  # two sections
        assert result["upserted_points"] == 2

    @patch("app.rag.ingest._get_qdrant_client")
    @patch("app.rag.ingest.embed_batch", side_effect=_fake_embed_batch)
    def test_empty_directory(
        self,
        mock_embed: MagicMock,
        mock_get_client: MagicMock,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_ingestion(tmpdir)
        assert result == {"total_docs": 0, "total_chunks": 0, "upserted_points": 0}

    @patch("app.rag.ingest._get_qdrant_client")
    @patch("app.rag.ingest.embed_batch", side_effect=_fake_embed_batch)
    def test_idempotency_upsert_same_points_twice(
        self,
        mock_embed: MagicMock,
        mock_get_client: MagicMock,
    ) -> None:
        """Verify that re-running on unchanged files upserts the same number of points."""
        fake_client = MagicMock()
        fake_client.get_collections.return_value.collections = []
        mock_get_client.return_value = fake_client

        with tempfile.TemporaryDirectory() as tmpdir:
            doc_path = os.path.join(tmpdir, "stable.md")
            with open(doc_path, "w", encoding="utf-8") as f:
                f.write("# Title\n## FAQ\nSame content always.\n")

            run1 = run_ingestion(tmpdir)
            run2 = run_ingestion(tmpdir)

        assert run1["total_chunks"] == run2["total_chunks"]
        assert run1["upserted_points"] == run2["upserted_points"]
        assert run1["upserted_points"] == run1["total_chunks"]
