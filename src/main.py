"""FastAPI application entry point.

This is the composition root — where all dependencies are wired together.
The application factory pattern keeps the app testable and configurable.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.agents.graph import build_swarm
from src.api.middleware import setup_middleware
from src.api.v1.routes import chat, health
from src.domain.ports.knowledge_store import KnowledgeStore
from src.infrastructure.persistence.in_memory_ticket_repo import InMemoryTicketRepository
from src.infrastructure.persistence.in_memory_user_repo import InMemoryUserRepository
from src.infrastructure.search.duckduckgo_searcher import DuckDuckGoSearcher
from src.infrastructure.vector_store.chroma_store import ChromaKnowledgeStore
from src.settings import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ============================================================================
# Dependency Singletons (Composition Root)
# ============================================================================

_knowledge_store: ChromaKnowledgeStore | None = None
_swarm = None


def get_knowledge_store() -> ChromaKnowledgeStore:
    """Get or create the knowledge store singleton."""
    global _knowledge_store
    if _knowledge_store is None:
        _knowledge_store = ChromaKnowledgeStore()
    return _knowledge_store


def get_swarm():
    """Get or create the agent swarm singleton."""
    global _swarm
    if _swarm is None:
        _swarm = build_swarm(
            knowledge_store=get_knowledge_store(),
            web_searcher=DuckDuckGoSearcher(),
            user_repo=InMemoryUserRepository(),
            ticket_repo=InMemoryTicketRepository(),
        )
    return _swarm


# ============================================================================
# Application Factory
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — startup and shutdown events."""
    logger.info("🚀 Starting Infinity Agent Swarm...")
    logger.info("   Environment: %s", settings.app_env)
    logger.info("   Guardrails: %s", "enabled" if settings.enable_guardrails else "disabled")

    # Validate configuration
    if not settings.openrouter_api_key:
        logger.warning("⚠️  OPENROUTER_API_KEY is not set — LLM calls will fail!")
    else:
        logger.info("   OpenRouter API: configured ✅")

    # Initialize singletons
    store = get_knowledge_store()
    stats = await store.get_collection_stats()
    logger.info("   Knowledge Base: %d documents ✅", stats["count"])

    if stats["count"] == 0:
        logger.warning(
            "⚠️  Knowledge base is empty! Run: python -m scripts.ingest"
        )

    # Build the swarm
    get_swarm()
    logger.info("   Agent Swarm: ready ✅")
    logger.info("🟢 Infinity Agent is ready at http://%s:%d", settings.app_host, settings.app_port)

    yield

    logger.info("🔴 Shutting down Infinity Agent...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Infinity Agent — InfinitePay AI Swarm",
        description=(
            "Multi-agent AI system for InfinitePay customer service. "
            "Routes user messages through specialized agents: "
            "Knowledge (RAG), Customer Support, and Sentiment Analysis."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Middleware
    setup_middleware(app)

    # API Routes (v1)
    app.include_router(chat.router, prefix="/v1")
    app.include_router(health.router, prefix="/v1")

    # Static files for frontend (if the directory exists)
    import os

    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
    if os.path.exists(frontend_path):
        app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

    return app


# Application instance
app = create_app()
