"""Tests for knowledge-node web fallback heuristics."""

from __future__ import annotations

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from src.agents.nodes import knowledge_node as knowledge_module
from src.domain.ports.web_searcher import WebSearchResult


def test_detect_infinitepay_domain_query() -> None:
    assert knowledge_module._is_infinitepay_query("Quais as taxas da maquininha?") is True
    assert knowledge_module._is_infinitepay_query("Como funciona o InfiniteTap?") is True


def test_detect_non_infinitepay_query() -> None:
    assert knowledge_module._is_infinitepay_query("Quais as principais noticias de Sao Paulo hoje?") is False


def test_detect_echo_response() -> None:
    user = "Quais as principais noticias de Sao Paulo hoje?"
    llm = "Quais as principais noticias de Sao Paulo hoje?"
    assert knowledge_module._looks_like_echo_response(user, llm) is True


def test_detect_non_echo_response() -> None:
    user = "Quais as principais noticias de Sao Paulo hoje?"
    llm = "Aqui estao os destaques de hoje em Sao Paulo com fontes externas."
    assert knowledge_module._looks_like_echo_response(user, llm) is False


@pytest.mark.asyncio
async def test_general_query_uses_deterministic_web_search(monkeypatch) -> None:
    class _FakeLLM:
        async def ainvoke(self, _messages):
            return AIMessage(content="Resumo das notícias com fontes.")

    class _FakeWebSearcher:
        async def search(self, _query, max_results=5):  # noqa: ARG002
            return [
                WebSearchResult(
                    title="Notícia A",
                    url="https://example.com/a",
                    snippet="Resumo A",
                ),
                WebSearchResult(
                    title="Notícia B",
                    url="https://example.com/b",
                    snippet="Resumo B",
                ),
            ]

    monkeypatch.setattr(knowledge_module, "get_knowledge_llm", lambda: _FakeLLM())
    node = knowledge_module.create_knowledge_node(
        knowledge_store=object(),
        web_searcher=_FakeWebSearcher(),
    )

    state = {
        "messages": [HumanMessage(content="Quais as principais notícias de São Paulo hoje?")],
        "user_id": "client_web",
        "intent": "knowledge",
        "language": "pt-BR",
        "agent_route": "knowledge",
        "sentiment_score": 0.0,
        "escalated": False,
        "guardrail_blocked": False,
        "guardrail_reason": "",
        "metadata": {},
    }

    result = await node(state)
    assert result["metadata"]["knowledge_deterministic_web_search"] is True
    assert result["metadata"]["knowledge_web_results_count"] == 2
    assert "Resumo das notícias" in result["messages"][0].content
