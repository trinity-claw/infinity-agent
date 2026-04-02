"""Domain model for chat messages and responses.

These are pure Value Objects — immutable data containers with no behavior
beyond validation. They represent the core communication protocol of the swarm.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.domain.models.enums import AgentType, GuardrailAction


@dataclass(frozen=True)
class ChatMessage:
    """Incoming user message — the primary input to the swarm."""

    message: str
    user_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.message.strip():
            raise ValueError("Message cannot be empty")
        if not self.user_id.strip():
            raise ValueError("User ID cannot be empty")


@dataclass(frozen=True)
class ChatResponse:
    """Agent swarm response — the primary output from the swarm."""

    response: str
    agent_used: AgentType
    intent: str
    language: str = "pt-BR"
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class GuardrailResult:
    """Result of a guardrail check (input or output)."""

    action: GuardrailAction
    reason: str = ""
    category: str = "safe"
    original_content: str = ""
    sanitized_content: str | None = None


@dataclass(frozen=True)
class RetrievedChunk:
    """A single chunk retrieved from the knowledge base via RAG."""

    content: str
    source_url: str
    relevance_score: float
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def citation(self) -> str:
        """Format as a markdown citation."""
        return f"[Source: {self.source_url}]"
