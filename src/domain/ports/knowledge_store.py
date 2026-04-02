"""Port: Knowledge Store interface.

Defines the contract for vector database operations (RAG retrieval).
"""

from abc import ABC, abstractmethod
from typing import Any

from src.domain.models.chat import RetrievedChunk


class KnowledgeStore(ABC):
    """Abstract interface for the vector knowledge base."""

    @abstractmethod
    async def search(self, query: str, k: int = 5) -> list[RetrievedChunk]:
        """Perform similarity search and return the top-k most relevant chunks."""
        ...

    @abstractmethod
    async def add_documents(
        self,
        texts: list[str],
        metadatas: list[dict[str, Any]],
        ids: list[str],
    ) -> None:
        """Add documents to the knowledge store."""
        ...

    @abstractmethod
    async def get_collection_stats(self) -> dict[str, Any]:
        """Return statistics about the knowledge store (doc count, etc.)."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the knowledge store is operational."""
        ...
