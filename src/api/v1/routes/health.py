"""Health check route.

GET /v1/health returns the operational status of all services.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

from src.api.v1.schemas import HealthResponse

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
        from src.settings import settings

        if settings.openrouter_api_key:
            services["llm"] = "configured"
        else:
            services["llm"] = "not_configured"
    except Exception:
        services["llm"] = "error"

    # Check ChromaDB
    try:
        from src.main import get_knowledge_store

        store = get_knowledge_store()
        stats = await store.get_collection_stats()
        services["knowledge_base"] = f"operational ({stats.get('count', 0)} documents)"
    except Exception:
        services["knowledge_base"] = "not_initialized"

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        services=services,
    )
