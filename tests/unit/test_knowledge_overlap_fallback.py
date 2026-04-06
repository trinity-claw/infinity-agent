"""Tests for knowledge-node fallback on support-style overlap queries."""

from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage

from src.agents.nodes import knowledge_node as knowledge_module


@pytest.mark.parametrize(
    "message",
    [
        "Qual o status dos servicos da InfinitePay hoje?",
        "Nao consigo acessar minha conta agora",
        "Is service down right now?",
        "I can't sign in and transfers are failing",
    ],
)
def test_support_overlap_detector(message: str) -> None:
    """Support-style prompts should trigger overlap detector."""
    assert knowledge_module._is_support_overlap_query(message) is True


@pytest.mark.asyncio
async def test_knowledge_overlap_fallback_skips_llm(monkeypatch) -> None:
    """When overlap is detected, node should return safe support guidance directly."""

    class _FailIfCalled:
        def bind_tools(self, *_args, **_kwargs):  # pragma: no cover - defensive
            raise AssertionError("Knowledge LLM should not be called for overlap fallback")

    monkeypatch.setattr(knowledge_module, "get_knowledge_llm", lambda: _FailIfCalled())

    node = knowledge_module.create_knowledge_node(knowledge_store=object(), web_searcher=object())
    state = {
        "messages": [HumanMessage(content="Qual o status dos servicos da InfinitePay hoje?")],
        "user_id": "client_test",
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
    content = result["messages"][0].content.lower()

    assert "suporte" in content or "support" in content
    assert result["metadata"]["knowledge_overlap_fallback"] is True
