"""
CLI entrypoint that ingests every markdown document in docs/ into Qdrant
by calling app/rag/ingest.py. Run once after docker compose up.

Usage::

    python scripts/run_ingestion.py [docs_dir]

If *docs_dir* is omitted, defaults to ``docs/``.
"""

import sys

from app.rag.ingest import run_ingestion


def main() -> None:
    docs_dir = sys.argv[1] if len(sys.argv) > 1 else "docs/"
    result = run_ingestion(docs_dir)
    if result["total_docs"] == 0:
        print(f"No markdown files found in '{docs_dir}'.")
        sys.exit(1)


if __name__ == "__main__":
    main()
