from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    auth_router,
    authors_router,
    debug_router,
    ebooks_router,
    genres_router,
    health_router,
    manuscripts_router,
    samples_router,
)
from app.api.errors import register_error_handlers
from app.config import settings

app = FastAPI(
    title="Self-Publishing Platform",
    description="A self-publishing platform for authors to share their work",
    version="0.1.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register global error handlers
register_error_handlers(app)

# Health check
app.include_router(health_router, prefix="/health", tags=["health"])

# Auth endpoints
app.include_router(auth_router, prefix="/auth", tags=["auth"])

# Author profile endpoints
app.include_router(authors_router, prefix="/authors", tags=["authors"])

# Manuscript management
app.include_router(manuscripts_router, prefix="/manuscripts", tags=["manuscripts"])
app.include_router(genres_router, prefix="/genres", tags=["genres"])

# Sample definitions
app.include_router(samples_router, prefix="/samples", tags=["samples"])

# Ebook management and downloads
app.include_router(ebooks_router, prefix="/ebooks", tags=["ebooks"])

# Debug endpoints (dev only)
if settings.ENVIRONMENT == "dev":
    app.include_router(debug_router, prefix="/debug", tags=["debug"])
