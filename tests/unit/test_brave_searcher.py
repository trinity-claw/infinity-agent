"""Unit tests for Brave web search adapter."""

from __future__ import annotations

import pytest

from src.infrastructure.search.brave_searcher import BraveSearcher


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class _FakeAsyncClient:
    def __init__(self, payload: dict):
        self._payload = payload
        self.called = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, *_args, **_kwargs):
        self.called = True
        return _FakeResponse(self._payload)


@pytest.mark.asyncio
async def test_brave_search_returns_empty_when_api_key_missing() -> None:
    searcher = BraveSearcher(api_key="")
    results = await searcher.search("noticias sao paulo", max_results=3)
    assert results == []


@pytest.mark.asyncio
async def test_brave_search_parses_web_results(monkeypatch) -> None:
    payload = {
        "web": {
            "results": [
                {
                    "title": "Noticia 1",
                    "url": "https://example.com/1",
                    "description": "Resumo 1",
                },
                {
                    "title": "Noticia 2",
                    "url": "https://example.com/2",
                    "extra_snippets": ["Linha A", "Linha B"],
                },
            ]
        }
    }
    fake_client = _FakeAsyncClient(payload)

    monkeypatch.setattr(
        "src.infrastructure.search.brave_searcher.httpx.AsyncClient",
        lambda **_kwargs: fake_client,
    )

    searcher = BraveSearcher(api_key="token-123")
    results = await searcher.search("noticias sao paulo", max_results=3)

    assert fake_client.called is True
    assert len(results) == 2
    assert results[0].title == "Noticia 1"
    assert results[0].url == "https://example.com/1"
    assert results[0].snippet == "Resumo 1"
    assert results[1].snippet == "Linha A Linha B"
