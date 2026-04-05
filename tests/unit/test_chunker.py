"""Unit tests for the RAG text chunker."""

import pytest

from src.rag.chunker import TextChunk, chunk_page
from src.rag.scraper import ScrapedPage


def make_page(content: str, url: str = "https://infinitepay.io/test") -> ScrapedPage:
    return ScrapedPage(url=url, title="Test Page", content=content, section="test")


class TestChunkPage:
    def test_empty_content_returns_no_chunks(self):
        page = make_page("")
        result = chunk_page(page)
        assert result == []

    def test_short_content_returns_single_chunk(self):
        page = make_page("Conteúdo curto de teste.")
        result = chunk_page(page)
        assert len(result) == 1
        assert result[0].content == "Conteúdo curto de teste."

    def test_long_content_splits_into_chunks(self):
        # Create content larger than default chunk_size (512 chars)
        long_text = "\n".join([f"Parágrafo número {i} com conteúdo de exemplo." for i in range(30)])
        page = make_page(long_text)
        result = chunk_page(page, chunk_size=200, chunk_overlap=30)
        assert len(result) > 1

    def test_chunk_metadata_has_source_url(self):
        page = make_page("Algum conteúdo.", url="https://infinitepay.io/maquininha")
        result = chunk_page(page)
        assert result[0].metadata["source_url"] == "https://infinitepay.io/maquininha"

    def test_chunk_metadata_has_section(self):
        page = ScrapedPage(
            url="https://infinitepay.io/pix",
            title="Pix",
            content="Pix é gratuito.",
            section="pix",
        )
        result = chunk_page(page)
        assert result[0].metadata["section"] == "pix"

    def test_chunk_ids_are_unique(self):
        long_text = "\n".join([f"Linha {i} " * 20 for i in range(50)])
        page = make_page(long_text)
        result = chunk_page(page, chunk_size=200, chunk_overlap=20)
        ids = [c.chunk_id for c in result]
        assert len(ids) == len(set(ids)), "Chunk IDs should be unique"

    def test_chunk_id_deterministic(self):
        page = make_page("Mesmo conteúdo sempre gera o mesmo ID.")
        r1 = chunk_page(page)
        r2 = chunk_page(page)
        assert r1[0].chunk_id == r2[0].chunk_id

    def test_chunks_contain_original_content(self):
        text = "Taxa de débito: 1.37%\nTaxa de crédito: 3.15%\nPix: gratuito"
        page = make_page(text)
        result = chunk_page(page)
        full = " ".join(c.content for c in result)
        assert "1.37%" in full
        assert "3.15%" in full

    def test_chunk_size_respected(self):
        # Use newline-separated paragraphs so the chunker can split them
        long_text = "\n".join(["palavra " * 15 for _ in range(50)])
        page = make_page(long_text)
        result = chunk_page(page, chunk_size=100, chunk_overlap=10)
        assert len(result) > 1
        for chunk in result:
            # Each chunk should not wildly exceed the target size (allow overlap slack)
            assert len(chunk.content) <= 300
