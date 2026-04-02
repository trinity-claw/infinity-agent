"""Port: Web Searcher interface.

Defines the contract for external web search operations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class WebSearchResult:
    """A single result from a web search."""

    title: str
    url: str
    snippet: str


class WebSearcher(ABC):
    """Abstract interface for web search."""

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> list[WebSearchResult]:
        """Perform a web search and return results."""
        ...
