"""API middleware.

CORS configuration and request logging.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.settings import settings


def setup_middleware(app: FastAPI) -> None:
    """Configure all middleware for the FastAPI application."""
    origins_raw = (settings.cors_allow_origins or "").strip()

    if not origins_raw or origins_raw == "*":
        allow_origins = ["*"]
        allow_credentials = False
    else:
        allow_origins = [origin.strip() for origin in origins_raw.split(",") if origin.strip()]
        allow_credentials = True

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
