"""Unit tests for dependency container checkpointer lifecycle."""

from __future__ import annotations

from unittest.mock import patch

import pytest

import src.container as container


class FakeAsyncContextManager:
    """Minimal async context manager used to mock AsyncSqliteSaver factory."""

    def __init__(self, value):
        self.value = value
        self.enter_calls = 0
        self.exit_calls = 0

    async def __aenter__(self):
        self.enter_calls += 1
        return self.value

    async def __aexit__(self, exc_type, exc, tb):
        self.exit_calls += 1
        return False


@pytest.fixture(autouse=True)
def reset_container_singletons():
    """Reset module-level singletons so each test starts clean."""
    container._knowledge_store = None
    container._checkpointer_cm = None
    container._checkpointer = None
    container._checkpointer_failed = False
    container._swarm = None


@pytest.mark.asyncio
async def test_get_checkpointer_initializes_from_async_context_manager():
    saver = object()
    context_manager = FakeAsyncContextManager(saver)

    with patch(
        "langgraph.checkpoint.sqlite.aio.AsyncSqliteSaver.from_conn_string",
        return_value=context_manager,
    ) as from_conn_string:
        first = await container.get_checkpointer()
        second = await container.get_checkpointer()

    assert first is saver
    assert second is saver
    assert context_manager.enter_calls == 1
    from_conn_string.assert_called_once()


@pytest.mark.asyncio
async def test_close_checkpointer_closes_async_context_manager():
    saver = object()
    context_manager = FakeAsyncContextManager(saver)

    with patch(
        "langgraph.checkpoint.sqlite.aio.AsyncSqliteSaver.from_conn_string",
        return_value=context_manager,
    ):
        await container.get_checkpointer()

    await container.close_checkpointer()

    assert context_manager.exit_calls == 1
    assert container._checkpointer is None
    assert container._checkpointer_cm is None
    assert container._checkpointer_failed is False


@pytest.mark.asyncio
async def test_get_swarm_falls_back_to_none_when_checkpointer_init_fails():
    fake_swarm = object()

    with patch(
        "langgraph.checkpoint.sqlite.aio.AsyncSqliteSaver.from_conn_string",
        side_effect=RuntimeError("db down"),
    ), patch("src.container.get_knowledge_store", return_value=object()), patch(
        "src.container.DuckDuckGoSearcher", return_value=object()
    ), patch(
        "src.container.InMemoryUserRepository", return_value=object()
    ), patch(
        "src.container.InMemoryTicketRepository", return_value=object()
    ), patch(
        "src.agents.graph.build_swarm", return_value=fake_swarm
    ) as build_swarm:
        swarm = await container.get_swarm()

    assert swarm is fake_swarm
    assert container._checkpointer_failed is True
    assert build_swarm.call_args.kwargs["checkpointer"] is None
