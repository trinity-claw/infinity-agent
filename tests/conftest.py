"""Shared pytest fixtures."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_swarm():
    """Mock LangGraph swarm that returns a predictable response."""
    swarm = MagicMock()
    swarm.ainvoke = AsyncMock(return_value={
        "messages": [
            MagicMock(
                content="Resposta de teste do agente de conhecimento.",
                name="knowledge",
            )
        ],
        "intent": "knowledge",
        "language": "pt-BR",
        "agent_route": "knowledge",
        "escalated": False,
        "guardrail_blocked": False,
        "metadata": {},
    })
    return swarm


@pytest.fixture
def app(mock_swarm):
    """FastAPI test app with mocked swarm."""
    with patch("src.main.get_swarm", return_value=mock_swarm), \
         patch("src.main.get_knowledge_store") as mock_store:

        mock_store.return_value.get_collection_stats = AsyncMock(return_value={"count": 42})
        mock_store.return_value.health_check = AsyncMock(return_value=True)

        from src.main import create_app
        return create_app()


@pytest.fixture
def client(app):
    """FastAPI TestClient."""
    return TestClient(app)
