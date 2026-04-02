"""DuckDuckGo Web Searcher implementation.

Implements the WebSearcher port using DuckDuckGo — free, no API key required.
"""

from duckduckgo_search import DDGS

from src.domain.ports.web_searcher import WebSearcher, WebSearchResult


class DuckDuckGoSearcher(WebSearcher):
    """Web search via DuckDuckGo — zero-cost, zero-config."""

    def __init__(self, region: str = "br-pt") -> None:
        self._region = region

    async def search(self, query: str, max_results: int = 5) -> list[WebSearchResult]:
        """Perform a DuckDuckGo web search."""
        try:
            with DDGS() as ddgs:
                raw_results = list(
                    ddgs.text(query, region=self._region, max_results=max_results)
                )

            return [
                WebSearchResult(
                    title=r.get("title", ""),
                    url=r.get("href", ""),
                    snippet=r.get("body", ""),
                )
                for r in raw_results
            ]
        except Exception:
            # Graceful degradation — return empty on search failure
            return []
