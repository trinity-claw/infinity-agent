"""Text chunking strategies for RAG ingestion.

Splits scraped content into overlapping chunks optimized for
vector similarity search.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from src.rag.scraper import ScrapedPage


@dataclass
class TextChunk:
    """A chunk of text ready for embedding and storage."""

    chunk_id: str
    content: str
    metadata: dict


def chunk_page(
    page: ScrapedPage,
    chunk_size: int = 512,
    chunk_overlap: int = 100,
) -> list[TextChunk]:
    """Split a scraped page into overlapping chunks.

    Uses a simple character-based splitting strategy with overlap
    to maintain context across chunk boundaries.

    Args:
        page: The scraped page to chunk.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Number of overlapping characters between chunks.

    Returns:
        List of TextChunk objects with metadata.
    """
    text = page.content
    chunks: list[TextChunk] = []

    if not text:
        return chunks

    # Split by paragraphs first, then recombine to fit chunk_size
    paragraphs = text.split("\n")
    current_chunk = ""
    chunk_index = 0

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        # If adding this paragraph would exceed chunk_size, finalize current chunk
        if current_chunk and len(current_chunk) + len(paragraph) + 1 > chunk_size:
            chunk_id = _generate_chunk_id(page.url, chunk_index)
            chunks.append(
                TextChunk(
                    chunk_id=chunk_id,
                    content=current_chunk.strip(),
                    metadata={
                        "source_url": page.url,
                        "page_title": page.title,
                        "section": page.section,
                        "chunk_index": chunk_index,
                    },
                )
            )

            # Keep overlap from the end of the current chunk
            if chunk_overlap > 0 and len(current_chunk) > chunk_overlap:
                current_chunk = current_chunk[-chunk_overlap:] + "\n" + paragraph
            else:
                current_chunk = paragraph

            chunk_index += 1
        else:
            current_chunk = (
                current_chunk + "\n" + paragraph if current_chunk else paragraph
            )

    # Don't forget the last chunk
    if current_chunk.strip():
        chunk_id = _generate_chunk_id(page.url, chunk_index)
        chunks.append(
            TextChunk(
                chunk_id=chunk_id,
                content=current_chunk.strip(),
                metadata={
                    "source_url": page.url,
                    "page_title": page.title,
                    "section": page.section,
                    "chunk_index": chunk_index,
                },
            )
        )

    return chunks


def _generate_chunk_id(url: str, index: int) -> str:
    """Generate a deterministic chunk ID for upsert idempotency."""
    raw = f"{url}:{index}"
    return hashlib.md5(raw.encode()).hexdigest()
