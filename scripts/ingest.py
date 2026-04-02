"""RAG Ingestion Script.

Run this script to scrape InfinitePay website content and populate
the ChromaDB knowledge base.

Usage:
    python -m scripts.ingest
"""

import asyncio
import logging
import sys

# Add project root to path
sys.path.insert(0, ".")

from src.infrastructure.vector_store.chroma_store import ChromaKnowledgeStore
from src.rag.ingest_pipeline import ingest_knowledge_base


async def main() -> None:
    """Run the RAG ingestion pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )

    store = ChromaKnowledgeStore()
    result = await ingest_knowledge_base(store)

    print("\n📊 Ingestion Summary:")
    print(f"   Pages scraped:    {result['pages_scraped']}")
    print(f"   Chunks created:   {result['chunks_created']}")
    print(f"   Documents stored: {result['documents_stored']}")


if __name__ == "__main__":
    asyncio.run(main())
