"""Input Guardrail node.

Validates user messages before they reach the agent swarm.
Uses NeMo Guardrails for comprehensive input protection.
"""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage

from src.agents.guardrails.blocklist import BLOCKED_TOPICS, INJECTION_PATTERNS
from src.agents.state import AgentState
from src.settings import settings

logger = logging.getLogger(__name__)


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

    # Check for prompt injection (compare lowercase to lowercase)
    for pattern in INJECTION_PATTERNS:
        if pattern.lower() in content:
            logger.warning("Input guardrail: prompt injection detected: %s", pattern)
            return {
                "guardrail_blocked": True,
                "guardrail_reason": f"Prompt injection detected: {pattern}",
                "messages": [
                    AIMessage(
                        content=(
                            "Desculpe, só posso ajudar com perguntas sobre os produtos, "
                            "serviços e suporte da InfinitePay. "
                            "Como posso te ajudar?"
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
                            "Fui desenvolvido para ajudar com perguntas sobre a InfinitePay "
                            "e questões gerais de conhecimento. Não consigo ajudar com esse "
                            "assunto específico. Em que mais posso te ajudar?"
                        ),
                        name="guardrail",
                    )
                ],
            }

    return {"guardrail_blocked": False, "guardrail_reason": ""}
