"""
FastAPI app entrypoint: creates the app, includes the chat/tickets/
escalations/auth routers, and registers startup checks.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.accounts import router as accounts_router
from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.escalations import router as escalations_router
from app.api.routes.products import router as products_router
from app.api.routes.tickets import router as tickets_router

logger = logging.getLogger(__name__)

app = FastAPI(title="Enterprise Customer Support AI Agent")


@app.on_event("startup")
def warmup():
    """Pre-load heavy models at startup so the first request isn't penalised."""
    logger.info("Pre-loading embedding model…")
    from app.rag.embedder import get_model
    get_model()
    logger.info("Embedding model loaded.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(accounts_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(escalations_router)
app.include_router(products_router)
app.include_router(tickets_router)
