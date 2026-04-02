"""RAG Ingestion Pipeline.

Orchestrates the full ingestion flow:
1. Scrape InfinitePay URLs
2. Chunk the content
3. Store in ChromaDB
"""

from __future__ import annotations

import logging

from src.domain.ports.knowledge_store import KnowledgeStore
from src.rag.chunker import chunk_page
from src.rag.scraper import ScrapedPage, scrape_pages

logger = logging.getLogger(__name__)


async def ingest_knowledge_base(
    knowledge_store: KnowledgeStore,
    urls: list[str] | None = None,
    chunk_size: int = 512,
    chunk_overlap: int = 100,
) -> dict:
    """Run the full RAG ingestion pipeline.

    Args:
        knowledge_store: The vector store to ingest into.
        urls: URLs to scrape (defaults to all InfinitePay URLs).
        chunk_size: Characters per chunk.
        chunk_overlap: Overlap between chunks.

    Returns:
        Summary statistics of the ingestion.
    """
    logger.info("=" * 60)
    logger.info("Starting RAG ingestion pipeline")
    logger.info("=" * 60)

    # Step 1: Scrape pages
    pages: list[ScrapedPage] = await scrape_pages(urls)
    logger.info("Step 1 complete: Scraped %d pages", len(pages))

    # Step 2: Chunk content
    all_chunks = []
    for page in pages:
        chunks = chunk_page(page, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        all_chunks.extend(chunks)
        logger.info("  Chunked %s → %d chunks", page.title, len(chunks))

    logger.info("Step 2 complete: Created %d total chunks", len(all_chunks))

    # Step 3: Store in ChromaDB (in batches)
    batch_size = 50
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i : i + batch_size]
        await knowledge_store.add_documents(
            texts=[c.content for c in batch],
            metadatas=[c.metadata for c in batch],
            ids=[c.chunk_id for c in batch],
        )
        logger.info("  Stored batch %d/%d", i // batch_size + 1, (len(all_chunks) - 1) // batch_size + 1)

    stats = await knowledge_store.get_collection_stats()
    logger.info("Step 3 complete: Knowledge base now has %d documents", stats["count"])
    logger.info("=" * 60)
    logger.info("RAG ingestion complete!")
    logger.info("=" * 60)

    return {
        "pages_scraped": len(pages),
        "chunks_created": len(all_chunks),
        "documents_stored": stats["count"],
    }
