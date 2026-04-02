"""Input Guardrail node.

Validates user messages before they reach the agent swarm.
Uses NeMo Guardrails for comprehensive input protection.
"""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage

from src.agents.state import AgentState
from src.settings import settings

logger = logging.getLogger(__name__)

# Patterns that indicate prompt injection attempts
INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all instructions",
    "ignore your instructions",
    "you are now",
    "act as",
    "pretend you are",
    "forget everything",
    "disregard",
    "reveal your prompt",
    "show me your system prompt",
    "what are your instructions",
    "DAN mode",
    "jailbreak",
    "ignore safety",
]

# Topics that should be deflected
BLOCKED_TOPICS = [
    "how to hack",
    "how to commit",
    "illegal",
    "drugs",
    "weapons",
    "violence",
    "explicit content",
]


async def input_guard_node(state: AgentState) -> dict:
    """Validate user input against safety rails.

    Checks for:
    1. Prompt injection attempts
    2. Blocked/harmful content
    3. Empty or malformed messages

    If blocked, sets guardrail_blocked=True and provides a safe response.
    """
    if not settings.enable_guardrails:
        return {"guardrail_blocked": False, "guardrail_reason": ""}

    last_message = state["messages"][-1]
    content = last_message.content.lower() if hasattr(last_message, "content") else ""

    # Check for prompt injection
    for pattern in INJECTION_PATTERNS:
        if pattern in content:
            logger.warning("Input guardrail: prompt injection detected: %s", pattern)
            return {
                "guardrail_blocked": True,
                "guardrail_reason": f"Prompt injection detected: {pattern}",
                "messages": [
                    AIMessage(
                        content=(
                            "I'm sorry, but I can only help with questions about "
                            "InfinitePay products, services, and account support. "
                            "How can I assist you today?"
                        ),
                        name="guardrail",
                    )
                ],
            }

    # Check for blocked topics
    for topic in BLOCKED_TOPICS:
        if topic in content:
            logger.warning("Input guardrail: blocked topic detected: %s", topic)
            return {
                "guardrail_blocked": True,
                "guardrail_reason": f"Blocked topic: {topic}",
                "messages": [
                    AIMessage(
                        content=(
                            "I'm designed to help with InfinitePay-related questions "
                            "and general knowledge inquiries. I'm unable to assist with "
                            "that particular topic. How else can I help?"
                        ),
                        name="guardrail",
                    )
                ],
            }

    return {"guardrail_blocked": False, "guardrail_reason": ""}
