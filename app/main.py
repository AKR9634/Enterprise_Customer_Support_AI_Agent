"""
FastAPI app entrypoint: creates the app, includes the chat/tickets/
escalations/auth routers, and registers startup checks.
"""

from fastapi import FastAPI

from app.api.routes.accounts import router as accounts_router
from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.products import router as products_router
from app.api.routes.tickets import router as tickets_router

app = FastAPI(title="Enterprise Customer Support AI Agent")

app.include_router(accounts_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(products_router)
app.include_router(tickets_router)
