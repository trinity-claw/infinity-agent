"""Unit tests for Promptfoo provider invocation config."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import tests.promptfoo_provider as provider


def test_promptfoo_provider_invokes_swarm_with_checkpointer_config():
    """Promptfoo provider must always pass configurable thread/checkpoint keys."""
    mock_swarm = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Resposta do conhecimento."
    mock_message.name = "knowledge"
    mock_swarm.ainvoke = AsyncMock(
        return_value={
            "messages": [mock_message],
            "intent": "knowledge",
            "guardrail_blocked": False,
        }
    )

    with patch(
        "tests.promptfoo_provider.container.get_swarm",
        new=AsyncMock(return_value=mock_swarm),
    ):
        result = provider.call_api("Quais sao os produtos?", {}, {})

    assert "output" in result
    payload = json.loads(result["output"])
    assert payload["agent_used"] == "knowledge"

    mock_swarm.ainvoke.assert_awaited_once()
    call_args = mock_swarm.ainvoke.call_args
    initial_state = call_args.args[0]
    config = call_args.kwargs["config"]

    assert initial_state["user_id"] == "promptfoo-tester"
    assert config["configurable"]["thread_id"] == "promptfoo-tester"
    assert config["configurable"]["checkpoint_ns"] == "promptfoo"
