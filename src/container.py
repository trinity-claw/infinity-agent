"""Dependency container — application-level singletons.

Extracts singleton creation from the application factory so that route
modules can import these helpers without creating a circular dependency:

    src.main → src.api.v1.routes.chat → src.main   ← circular (old)
    src.main → src.container ← src.api.v1.routes.chat  ← acyclic (new)
"""

from __future__ import annotations

from src.infrastructure.persistence.in_memory_ticket_repo import InMemoryTicketRepository
from src.infrastructure.persistence.in_memory_user_repo import InMemoryUserRepository
from src.infrastructure.search.duckduckgo_searcher import DuckDuckGoSearcher
from src.infrastructure.vector_store.chroma_store import ChromaKnowledgeStore

_knowledge_store: ChromaKnowledgeStore | None = None
_swarm = None


def get_knowledge_store() -> ChromaKnowledgeStore:
    """Return the ChromaDB knowledge store singleton (lazy-init)."""
    global _knowledge_store
    if _knowledge_store is None:
        _knowledge_store = ChromaKnowledgeStore()
    return _knowledge_store


def get_swarm():
    """Return the LangGraph agent swarm singleton (lazy-init).

    The import of build_swarm is deferred so that importing this module does
    not pull in LangGraph, all agent nodes, and the OpenRouter client until
    the first actual request — keeping test setup and CLI startup lightweight.
    """
    global _swarm
    if _swarm is None:
        from src.agents.graph import build_swarm

        _swarm = build_swarm(
            knowledge_store=get_knowledge_store(),
            web_searcher=DuckDuckGoSearcher(),
            user_repo=InMemoryUserRepository(),
            ticket_repo=InMemoryTicketRepository(),
        )
    return _swarm
