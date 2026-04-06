"""Health check and admin inspection routes.

GET /v1/health  — operational status of all services.
GET /v1/admin/knowledge — inspect ChromaDB collection (documents + sources).
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Query, Request

import src.container as container
from src.api.security import enforce_sensitive_endpoint_auth
from src.api.v1.schemas import HealthResponse
from src.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health check",
    description="Check the operational status of the Infinity Agent services.",
)
async def health_check() -> HealthResponse:
    """Health check endpoint — verifies all services are operational."""
    services: dict[str, str] = {}

    # Check LLM connectivity
    try:
        if settings.openrouter_api_key:
            services["llm"] = "configured"
        else:
            services["llm"] = "not_configured"
    except Exception:
        services["llm"] = "error"

    # Check web-search dependency (required for general-knowledge path)
    try:
        if settings.brave_search_api_key:
            services["web_search"] = "configured"
        else:
            services["web_search"] = "not_configured"
    except Exception:
        services["web_search"] = "error"

    # Check ChromaDB
    try:
        store = container.get_knowledge_store()
        stats = await store.get_collection_stats()
        services["knowledge_base"] = f"operational ({stats.get('count', 0)} documents)"
    except Exception:
        services["knowledge_base"] = "not_initialized"

    degraded_markers = ("not_configured", "error", "not_initialized")
    status = (
        "degraded"
        if any(any(marker in value for marker in degraded_markers) for value in services.values())
        else "healthy"
    )

    return HealthResponse(
        status=status,
        version="1.0.0",
        services=services,
    )


@router.get(
    "/admin/knowledge",
    summary="Inspect knowledge base contents",
    description=(
        "Returns a paginated preview of documents stored in ChromaDB, "
        "along with per-source chunk counts. Useful for verifying ingestion."
    ),
    response_model=dict[str, Any],
)
async def knowledge_admin(
    request: Request,
    limit: int = Query(20, ge=1, le=100, description="Documents per page"),
    offset: int = Query(0, ge=0, description="Page offset"),
) -> dict[str, Any]:
    """Admin endpoint: inspect what is stored in the ChromaDB knowledge base."""
    enforce_sensitive_endpoint_auth(request)
    store = container.get_knowledge_store()
    return await store.get_documents_preview(limit=limit, offset=offset)
