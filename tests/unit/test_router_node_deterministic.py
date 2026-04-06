"""Tests for deterministic router overrides on operational support queries."""

from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage

from src.agents.nodes import router_node as router_module


@pytest.mark.parametrize(
    "message",
    [
        "Qual o status atual dos servicos da InfinitePay?",
        "Tem instabilidade no Pix hoje?",
        "Is InfinitePay down right now?",
        "Service status is unstable today",
    ],
)
def test_operational_support_query_detector(message: str) -> None:
    """Operational status questions must match deterministic support detector."""
    assert router_module._is_operational_support_query(message) is True


@pytest.mark.asyncio
async def test_router_uses_deterministic_support_route_without_llm(monkeypatch) -> None:
    """For outage/status language, router should not call the LLM."""

    class _FailIfCalled:
        async def ainvoke(self, *_args, **_kwargs):  # pragma: no cover - defensive
            raise AssertionError("LLM should not be called for deterministic support route")

    monkeypatch.setattr(router_module, "get_router_llm", lambda: _FailIfCalled())

    state = {
        "messages": [HumanMessage(content="Qual o status atual dos servicos da InfinitePay?")],
        "user_id": "client_test",
        "intent": "",
        "language": "pt-BR",
        "agent_route": "",
        "sentiment_score": 0.0,
        "escalated": False,
        "guardrail_blocked": False,
        "guardrail_reason": "",
        "metadata": {},
    }

    result = await router_module.router_node(state)

    assert result["intent"] == "support"
    assert result["agent_route"] == "support"
    assert "deterministic" in result["messages"][0].content.lower()
