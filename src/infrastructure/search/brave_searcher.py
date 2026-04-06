"""Brave Search implementation for external web lookup."""

from __future__ import annotations

import logging

import httpx

from src.domain.ports.web_searcher import WebSearchResult, WebSearcher

logger = logging.getLogger(__name__)


class BraveSearcher(WebSearcher):
    """Web search via Brave Search API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.search.brave.com/res/v1/web/search",
    ) -> None:
        self._api_key = (api_key or "").strip()
        self._base_url = base_url

    async def search(self, query: str, max_results: int = 5) -> list[WebSearchResult]:
        """Perform a Brave web search."""
        if not self._api_key:
            logger.warning("Brave search API key is not configured; returning empty results")
            return []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    self._base_url,
                    headers={
                        "Accept": "application/json",
                        "X-Subscription-Token": self._api_key,
                    },
                    params={
                        "q": query,
                        "count": max_results,
                        "safesearch": "moderate",
                    },
                )
                response.raise_for_status()
                payload = response.json()

            raw_results = payload.get("web", {}).get("results", []) or []
            normalized: list[WebSearchResult] = []
            for item in raw_results:
                title = (item.get("title") or "").strip()
                url = (item.get("url") or "").strip()
                snippet = (item.get("description") or "").strip()
                if not snippet:
                    extra_snippets = item.get("extra_snippets") or []
                    if extra_snippets:
                        snippet = " ".join(str(s) for s in extra_snippets if s)
                if not title and not url and not snippet:
                    continue
                normalized.append(WebSearchResult(title=title, url=url, snippet=snippet))

            return normalized
        except Exception as exc:
            logger.warning("Brave search failed: %s", exc)
            return []
