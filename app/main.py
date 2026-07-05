"""
FastAPI app entrypoint: creates the app, includes the chat/tickets/
escalations/auth routers, and registers startup checks.
"""

from fastapi import FastAPI

from app.api.routes.auth import router as auth_router

app = FastAPI(title="Enterprise Customer Support AI Agent")

app.include_router(auth_router)
