"""Router Agent node.

Classifies user intent and routes to the appropriate specialized agent.
Uses structured output (JSON) for reliable classification.
"""

from __future__ import annotations

import json
import logging

from langchain_core.messages import AIMessage, SystemMessage

from src.agents.prompts.router_prompt import ROUTER_SYSTEM_PROMPT
from src.agents.routing_rules import is_operational_support_query
from src.agents.state import AgentState
from src.infrastructure.llm.model_factory import get_router_llm

logger = logging.getLogger(__name__)


def _is_operational_support_query(message: str) -> bool:
    """Backward-compatible local wrapper around shared routing rules."""
    return is_operational_support_query(message)


async def router_node(state: AgentState) -> dict:
    """Classify user intent and determine the target agent.

    Reads the last user message, classifies the intent, and sets
    the `intent` and `agent_route` fields in the state.

    Returns:
        State update with intent, language, and agent_route.
    """
    last_message = state["messages"][-1]
    raw_text = getattr(last_message, "content", "") or ""

    # Deterministic safety net: operational/status outage queries always go to support.
    if _is_operational_support_query(raw_text):
        logger.info(
            "Router deterministic override intent=support route=support for message=%s",
            raw_text[:120],
        )
        return {
            "intent": "support",
            "language": "pt-BR",
            "agent_route": "support",
            "messages": [
                AIMessage(
                    content=(
                        "[Router] Intent: support | Language: pt-BR | "
                        "Route: support (deterministic operational rule)"
                    ),
                    name="router",
                )
            ],
            "metadata": {
                **state.get("metadata", {}),
                "router_reasoning": "Deterministic rule for service status/outage query",
            },
        }

    llm = get_router_llm()

    response = await llm.ainvoke([
        SystemMessage(content=ROUTER_SYSTEM_PROMPT),
        last_message,
    ])

    # Parse the JSON classification
    try:
        content = response.content
        # Handle potential markdown code blocks in response
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        classification = json.loads(content.strip())
        intent = classification.get("intent", "knowledge")
        language = classification.get("language", "pt-BR")
        confidence = classification.get("confidence", 0.5)
        reasoning = classification.get("reasoning", "")

        logger.info(
            "Router classified intent=%s, language=%s, confidence=%.2f, reasoning=%s",
            intent,
            language,
            confidence,
            reasoning,
        )

    except (json.JSONDecodeError, AttributeError):
        # Fallback to knowledge agent if classification fails
        logger.warning("Router failed to parse classification, defaulting to knowledge")
        intent = "knowledge"
        language = "pt-BR"
        reasoning = "Classification parse failed, defaulting to knowledge"

    # Map intent to agent route
    route_map = {
        "knowledge": "knowledge",
        "general": "knowledge",
        "support": "support",
        "escalation": "escalation",
    }
    agent_route = route_map.get(intent, "knowledge")

    return {
        "intent": intent,
        "language": language,
        "agent_route": agent_route,
        "messages": [
            AIMessage(
                content=f"[Router] Intent: {intent} | Language: {language} | Route: {agent_route}",
                name="router",
            )
        ],
        "metadata": {
            **state.get("metadata", {}),
            "router_reasoning": reasoning,
        },
    }
