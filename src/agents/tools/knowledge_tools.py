"""Knowledge Agent tools.

Tools for RAG search and web search, created via factory pattern
to inject the KnowledgeStore and WebSearcher dependencies.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.tools import tool

if TYPE_CHECKING:
    from src.domain.ports.knowledge_store import KnowledgeStore
    from src.domain.ports.web_searcher import WebSearcher


def create_knowledge_tools(
    knowledge_store: KnowledgeStore,
    web_searcher: WebSearcher,
) -> list:
    """Factory that creates knowledge tools with injected dependencies.

    Args:
        knowledge_store: Vector store for RAG retrieval.
        web_searcher: Web search engine for general questions.

    Returns:
        List of LangChain tools bound to the provided dependencies.
    """

    @tool
    async def search_knowledge_base(query: str) -> str:
        """Search InfinitePay's internal knowledge base for product information.

        Use this tool for questions about InfinitePay products, services,
        pricing, rates, or features. Returns relevant documentation chunks.

        Args:
            query: The search query about InfinitePay products or services.
        """
        chunks = await knowledge_store.search(query, k=5)

        if not chunks:
            return "No relevant information found in the knowledge base."

        results = []
        for i, chunk in enumerate(chunks, 1):
            results.append(
                f"[{i}] (Score: {chunk.relevance_score:.2f}) "
                f"Source: {chunk.source_url}\n"
                f"{chunk.content}"
            )
        return "\n\n---\n\n".join(results)

    @tool
    async def search_web(query: str) -> str:
        """Search the internet for general knowledge questions.

        Use this tool for questions NOT related to InfinitePay, such as
        news, sports, weather, current events, or general knowledge.

        Args:
            query: The general knowledge search query.
        """
        results = await web_searcher.search(query, max_results=5)

        if not results:
            return "No web search results found."

        formatted = []
        for r in results:
            formatted.append(f"**{r.title}**\n{r.snippet}\nURL: {r.url}")
        return "\n\n".join(formatted)

    return [search_knowledge_base, search_web]
