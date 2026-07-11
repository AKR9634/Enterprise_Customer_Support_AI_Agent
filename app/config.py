import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "")
TEST_DATABASE_URL: str = os.getenv("TEST_DATABASE_URL", "")

JWT_SECRET: str = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_HOURS: int = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
QDRANT_URL: str = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
OPEN_ROUTER_API_KEY: str = os.getenv("OPEN_ROUTER_API_KEY", "")

# ── RAG / Ingestion ──────────────────────────────────────────────────────────
QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "knowledge_base")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))

# ── LLM Provider ─────────────────────────────────────────────────────────────
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
OPEN_ROUTER_BASE_URL: str = os.getenv("OPEN_ROUTER_BASE_URL", "https://openrouter.ai/api/v1")
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.0"))
LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "1024"))

# ── Graph / Escalation ────────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
ESCALATION_ACKNOWLEDGMENT: str = os.getenv(
    "ESCALATION_ACKNOWLEDGMENT",
    "Thank you for reaching out. We've escalated your request to a human agent who will follow up shortly.",
)

# ── LangSmith Tracing ──────────────────────────────────────────────────────────
LANGSMITH_TRACING: bool = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT", "Enterprise-Customer-Support-AI-Agent")
