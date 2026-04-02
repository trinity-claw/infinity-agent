"""ChromaDB Knowledge Store implementation.

Implements the KnowledgeStore port using ChromaDB for vector storage
and OpenAI embeddings via OpenRouter.
"""

from __future__ import annotations

import logging
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.domain.models.chat import RetrievedChunk
from src.domain.ports.knowledge_store import KnowledgeStore
from src.settings import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "infinitepay_knowledge"


class ChromaKnowledgeStore(KnowledgeStore):
    """ChromaDB-backed knowledge store for RAG retrieval.

    Uses ChromaDB's built-in embedding function for simplicity,
    with persistent storage for Docker deployments.
    """

    def __init__(self, persist_dir: str | None = None) -> None:
        self._persist_dir = persist_dir or settings.chroma_persist_dir

        # Initialize ChromaDB client with persistence
        self._client = chromadb.PersistentClient(
            path=self._persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # Get or create collection
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        logger.info(
            "ChromaDB initialized at %s with %d documents",
            self._persist_dir,
            self._collection.count(),
        )

    async def search(self, query: str, k: int = 5) -> list[RetrievedChunk]:
        """Perform similarity search against the knowledge base."""
        if self._collection.count() == 0:
            logger.warning("Knowledge base is empty — no documents to search")
            return []

        results = self._collection.query(
            query_texts=[query],
            n_results=min(k, self._collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        chunks = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0.0
                # Convert cosine distance to similarity score
                relevance = 1.0 - distance

                chunks.append(
                    RetrievedChunk(
                        content=doc,
                        source_url=metadata.get("source_url", ""),
                        relevance_score=relevance,
                        metadata=metadata,
                    )
                )

        return chunks

    async def add_documents(
        self,
        texts: list[str],
        metadatas: list[dict[str, Any]],
        ids: list[str],
    ) -> None:
        """Add documents to the ChromaDB collection."""
        self._collection.upsert(
            documents=texts,
            metadatas=metadatas,
            ids=ids,
        )
        logger.info("Added %d documents to knowledge base", len(texts))

    async def get_collection_stats(self) -> dict[str, Any]:
        """Return statistics about the knowledge store."""
        return {
            "count": self._collection.count(),
            "collection_name": COLLECTION_NAME,
            "persist_dir": self._persist_dir,
        }

    async def health_check(self) -> bool:
        """Check if ChromaDB is operational."""
        try:
            self._collection.count()
            return True
        except Exception:
            return False
