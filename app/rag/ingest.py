"""
Loads markdown documents, splits them into heading-aware chunks, embeds
each chunk via the singleton embedder, and upserts into Qdrant using
deterministic point IDs so re-runs are idempotent (no duplicate points).
"""

import hashlib
import os
import re
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
    QDRANT_URL,
)
from app.rag.embedder import embed_batch


def _parse_sections(content: str) -> list[dict[str, str]]:
    """Split content by ``## `` level-2 markdown headings.

    Returns a list of ``{"heading": str, "text": str}`` dicts. The text
    includes the heading line itself (for context) but the heading field
    stores only the heading title (without the ``## `` prefix).
    """
    lines = content.split("\n")
    sections: list[dict[str, str]] = []
    current_heading = ""
    current_lines: list[str] = []

    for line in lines:
        m = re.match(r"^## (.+)$", line)
        if m:
            if current_lines or current_heading:
                sections.append({
                    "heading": current_heading,
                    "text": "\n".join(current_lines).strip(),
                })
            current_heading = m.group(1).strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    text = "\n".join(current_lines).strip()
    if text:
        sections.append({
            "heading": current_heading,
            "text": text,
        })

    return sections


def _chunk_text_by_paragraphs(
    text: str,
    heading: str,
    chunk_size: int,
    overlap: int,
    start_index: int,
) -> list[dict[str, Any]]:
    """Split a long section into paragraph-boundary chunks with overlap."""
    paragraphs = re.split(r"\n\s*\n", text)
    chunks: list[dict[str, Any]] = []
    buffer = ""
    idx = start_index

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(buffer) + len(para) + 2 <= chunk_size:
            buffer = (buffer + "\n\n" + para).strip() if buffer else para
        else:
            if buffer:
                chunks.append({
                    "source": "",
                    "section": heading,
                    "chunk_index": idx,
                    "text": buffer,
                })
                idx += 1
            # overlap: carry last `overlap` chars into next buffer
            overlap_text = buffer[-overlap:] if len(buffer) > overlap else buffer
            buffer = (overlap_text + "\n\n" + para).strip() if overlap_text else para

    if buffer:
        chunks.append({
            "source": "",
            "section": heading,
            "chunk_index": idx,
            "text": buffer,
        })
        idx += 1

    return chunks


def _section_to_chunks(
    section: dict[str, str],
    source: str,
    chunk_size: int,
    overlap: int,
    start_index: int,
) -> list[dict[str, Any]]:
    """Convert one parsed section into one or more chunks."""
    heading = section["heading"]
    text = section["text"]
    if not text:
        return []

    if len(text) <= chunk_size:
        return [{
            "source": source,
            "section": heading,
            "chunk_index": start_index,
            "text": text,
        }]

    sub_chunks = _chunk_text_by_paragraphs(text, heading, chunk_size, overlap, start_index)
    for c in sub_chunks:
        c["source"] = source
    return sub_chunks


def _load_docs(docs_dir: str) -> list[dict[str, str]]:
    """Walk *docs_dir* and read every ``.md`` file."""
    docs: list[dict[str, str]] = []
    if not os.path.isdir(docs_dir):
        return docs

    for entry in sorted(os.listdir(docs_dir)):
        path = os.path.join(docs_dir, entry)
        if not entry.endswith(".md") or not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as fh:
            docs.append({"source": entry, "content": fh.read()})

    return docs


def _chunk_documents(
    docs: list[dict[str, str]],
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[dict[str, Any]]:
    """Convert loaded documents into heading-aware chunks."""
    all_chunks: list[dict[str, Any]] = []
    global_idx = 0

    for doc in docs:
        source = doc["source"]
        content = doc["content"]

        # Strip top-level # title line if present (not a heading section)
        content = re.sub(r"^# .+\n?", "", content, count=1).strip()

        sections = _parse_sections(content)
        for sec in sections:
            chunks = _section_to_chunks(sec, source, chunk_size, overlap, global_idx)
            all_chunks.extend(chunks)
            global_idx += len(chunks)

    return all_chunks


def _make_point_id(source: str, chunk_index: int) -> str:
    raw = f"{source}::{chunk_index}"
    return hashlib.md5(raw.encode()).hexdigest()


def _get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)


def _ensure_collection(
    client: QdrantClient,
    collection_name: str = QDRANT_COLLECTION,
) -> None:
    collections = [c.name for c in client.get_collections().collections]
    if collection_name not in collections:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )


def _upsert_chunks(
    chunks: list[dict[str, Any]],
    embeddings: list[list[float]],
    collection_name: str = QDRANT_COLLECTION,
) -> int:
    client = _get_qdrant_client()
    # Use the passed collection name to allow callers to override
    _ensure_collection(client, collection_name=collection_name)

    points = [
        PointStruct(
            id=_make_point_id(c["source"], c["chunk_index"]),
            vector=embeddings[i],
            payload={
                "source": c["source"],
                "section": c["section"],
                "chunk_index": c["chunk_index"],
                "text": c["text"],
            },
        )
        for i, c in enumerate(chunks)
    ]

    if points:
        client.upsert(collection_name=collection_name, points=points)

    return len(points)


def run_ingestion(
    docs_dir: str = "docs/",
    collection_name: str = QDRANT_COLLECTION,
) -> dict:
    """Load, chunk, embed, and upsert all markdown files from *docs_dir*.

    If *collection_name* is provided, it overrides the default
    ``QDRANT_COLLECTION`` config value (useful for tests).

    Returns a summary dict with keys ``total_docs``, ``total_chunks``,
    ``upserted_points``.
    """
    docs = _load_docs(docs_dir)
    total_docs = len(docs)

    if not docs:
        return {"total_docs": 0, "total_chunks": 0, "upserted_points": 0}

    chunks = _chunk_documents(docs)
    total_chunks = len(chunks)

    texts = [c["text"] for c in chunks]
    embeddings = embed_batch(texts)

    upserted = _upsert_chunks(chunks, embeddings, collection_name=collection_name)

    print(
        f"Ingested {total_docs} doc(s) \u2192 {total_chunks} chunk(s) "
        f"\u2192 upserted {upserted} point(s) to '{collection_name}'"
    )

    return {
        "total_docs": total_docs,
        "total_chunks": total_chunks,
        "upserted_points": upserted,
    }
