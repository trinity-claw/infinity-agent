"""Security helpers for sensitive API endpoints."""

from __future__ import annotations

import hmac
import logging

from fastapi import HTTPException, Request

from src.settings import settings

logger = logging.getLogger(__name__)
_DEV_BYPASS_WARNED = False


def _extract_api_key(request: Request) -> str:
    """Extract API key from common header/query names."""
    return (
        (request.headers.get("x-api-key") or "").strip()
        or (request.headers.get("apikey") or "").strip()
        or (request.query_params.get("apikey") or "").strip()
    )


def enforce_sensitive_endpoint_auth(request: Request) -> None:
    """Enforce auth for sensitive endpoints in production only."""
    global _DEV_BYPASS_WARNED  # noqa: PLW0603

    if not settings.is_production:
        if not _DEV_BYPASS_WARNED:
            logger.warning(
                "Sensitive endpoint auth bypassed because APP_ENV=%s (non-production).",
                settings.app_env,
            )
            _DEV_BYPASS_WARNED = True
        return

    expected = (settings.sensitive_api_key or "").strip()
    if not expected:
        logger.error("SENSITIVE_API_KEY is not configured in production")
        raise HTTPException(
            status_code=503,
            detail="Sensitive endpoint authentication is not configured.",
        )

    provided = _extract_api_key(request)
    if not provided:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=403, detail="Forbidden")
