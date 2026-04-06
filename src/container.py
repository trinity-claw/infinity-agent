"""Dependency container for application singletons.

Centralizes singleton creation to avoid circular imports and to keep
construction logic in one place.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from src.infrastructure.persistence.in_memory_ticket_repo import InMemoryTicketRepository
from src.infrastructure.persistence.in_memory_user_repo import InMemoryUserRepository
from src.infrastructure.search.brave_searcher import BraveSearcher
from src.infrastructure.vector_store.chroma_store import ChromaKnowledgeStore
from src.settings import settings

logger = logging.getLogger(__name__)

_knowledge_store: ChromaKnowledgeStore | None = None
_user_repo: InMemoryUserRepository | None = None
_checkpointer_cm: Any = None
_checkpointer: Any = None
_checkpointer_failed: bool = False
_swarm = None


def get_knowledge_store() -> ChromaKnowledgeStore:
    """Return the ChromaDB knowledge store singleton (lazy-init)."""
    global _knowledge_store
    if _knowledge_store is None:
        _knowledge_store = ChromaKnowledgeStore()
    return _knowledge_store


def get_user_repository() -> InMemoryUserRepository:
    """Return the user repository singleton (lazy-init)."""
    global _user_repo
    if _user_repo is None:
        _user_repo = InMemoryUserRepository()
    return _user_repo


async def get_checkpointer():
    """Return the SQLite checkpointer singleton.

    LangGraph's ``AsyncSqliteSaver.from_conn_string`` returns an async context
    manager. We keep both the context manager and the entered saver so we can
    close it on shutdown.
    """
    global _checkpointer_cm, _checkpointer, _checkpointer_failed

    if _checkpointer_failed:
        return None
    if _checkpointer is not None:
        return _checkpointer

    try:
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

        db_path = settings.sqlite_db_path
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        _checkpointer_cm = AsyncSqliteSaver.from_conn_string(db_path)
        _checkpointer = await _checkpointer_cm.__aenter__()
        logger.info("SQLite checkpointer initialized at %s", db_path)
        return _checkpointer
    except Exception as exc:
        logger.error("Failed to initialize SQLite checkpointer: %s", exc, exc_info=True)
        _checkpointer = None
        _checkpointer_cm = None
        _checkpointer_failed = True
        return None


async def close_checkpointer() -> None:
    """Close the SQLite checkpointer context if it is open."""
    global _checkpointer_cm, _checkpointer, _checkpointer_failed

    if _checkpointer_cm is not None:
        try:
            await _checkpointer_cm.__aexit__(None, None, None)
            logger.info("SQLite checkpointer closed")
        except Exception as exc:
            logger.warning("Error while closing SQLite checkpointer: %s", exc, exc_info=True)

    _checkpointer_cm = None
    _checkpointer = None
    _checkpointer_failed = False


def close_swarm() -> None:
    """Drop compiled swarm singleton so startup can rebuild it cleanly."""
    global _swarm
    _swarm = None


async def get_swarm():
    """Return the LangGraph agent swarm singleton (lazy-init)."""
    global _swarm
    if _swarm is None:
        from src.agents.graph import build_swarm

        checkpointer = None
        try:
            checkpointer = await get_checkpointer()
            if checkpointer is None:
                logger.warning(
                    "Proceeding without SQLite checkpoint persistence. "
                    "Conversation memory will not survive restarts."
                )
        except Exception as exc:
            logger.error("Checkpointer initialization crashed: %s", exc, exc_info=True)
            logger.warning(
                "Proceeding without SQLite checkpoint persistence. "
                "Conversation memory will not survive restarts."
            )
            checkpointer = None

        _swarm = build_swarm(
            knowledge_store=get_knowledge_store(),
            web_searcher=BraveSearcher(
                api_key=settings.brave_search_api_key,
                base_url=settings.brave_search_base_url,
            ),
            user_repo=get_user_repository(),
            ticket_repo=InMemoryTicketRepository(),
            checkpointer=checkpointer,
        )
    return _swarm
