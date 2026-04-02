"""Agent Swarm state schema.

Defines the shared state that flows through the LangGraph StateGraph.
All agent nodes read from and write to this state.
"""

from __future__ import annotations

from typing import Annotated, Any

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """Shared state for the agent swarm graph.

    This TypedDict defines every field that flows through the LangGraph.
    Agents read what they need and write back their results.

    Attributes:
        messages: Conversation history (accumulated via add_messages reducer).
        user_id: The user identifier from the request.
        intent: Classified intent (knowledge, support, general, escalation).
        language: Detected language of the user message (e.g., "pt-BR", "en").
        agent_route: Which agent should handle the request.
        sentiment_score: Sentiment score from -1.0 (very negative) to 1.0 (very positive).
        escalated: Whether the conversation has been escalated to a human.
        guardrail_blocked: Whether guardrails blocked the message.
        guardrail_reason: Reason for the guardrail block, if any.
        metadata: Additional context passed between agents.
    """

    messages: Annotated[list[AnyMessage], add_messages]
    user_id: str
    intent: str
    language: str
    agent_route: str
    sentiment_score: float
    escalated: bool
    guardrail_blocked: bool
    guardrail_reason: str
    metadata: dict[str, Any]
