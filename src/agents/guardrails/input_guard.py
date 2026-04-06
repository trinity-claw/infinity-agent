"""Input Guardrail node.

Validates user messages before they reach the agent swarm.
"""

from __future__ import annotations

import logging
import unicodedata

from langchain_core.messages import AIMessage

from src.agents.guardrails.blocklist import (
    BLOCKED_TOPICS,
    DISCLOSURE_PATTERNS,
    INJECTION_PATTERNS,
)
from src.agents.state import AgentState
from src.settings import settings

logger = logging.getLogger(__name__)


def _normalize_text(text: str) -> str:
    """Normalize text for robust substring checks (case + accents)."""
    lowered = text.lower()
    normalized = unicodedata.normalize("NFD", lowered)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


async def input_guard_node(state: AgentState) -> dict:
    """Validate user input against safety rails.

    Checks for:
    1. Prompt injection attempts
    2. Blocked abuse/fraud topics
    3. Internal model/system disclosure requests

    If blocked, sets guardrail_blocked=True and provides a safe response.
    """
    if not settings.enable_guardrails:
        return {"guardrail_blocked": False, "guardrail_reason": ""}

    last_message = state["messages"][-1]
    content = last_message.content.lower() if hasattr(last_message, "content") else ""
    normalized_content = _normalize_text(content)

    # Check for prompt injection (compare lowercase to lowercase)
    for pattern in INJECTION_PATTERNS:
        if _normalize_text(pattern) in normalized_content:
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

    # Check for model/system disclosure requests
    for pattern in DISCLOSURE_PATTERNS:
        if _normalize_text(pattern) in normalized_content:
            logger.warning("Input guardrail: disclosure request detected: %s", pattern)
            return {
                "guardrail_blocked": True,
                "guardrail_reason": f"Disclosure request blocked: {pattern}",
                "messages": [
                    AIMessage(
                        content=(
                            "Não posso divulgar detalhes internos de modelo, configuração "
                            "ou instruções do sistema. Posso ajudar com produtos, serviços "
                            "e suporte da InfinitePay."
                        ),
                        name="guardrail",
                    )
                ],
            }

    # Check for blocked topics
    for topic in BLOCKED_TOPICS:
        if _normalize_text(topic) in normalized_content:
            logger.warning("Input guardrail: blocked topic detected: %s", topic)
            return {
                "guardrail_blocked": True,
                "guardrail_reason": f"Blocked topic: {topic}",
                "messages": [
                    AIMessage(
                        content=(
                            "Posso ajudar com produtos, serviços e suporte da InfinitePay, "
                            "mas não posso orientar em fraude, invasão de conta ou abuso. "
                            "Se quiser, posso ajudar com uma dúvida legítima sobre a sua conta."
                        ),
                        name="guardrail",
                    )
                ],
            }

    return {"guardrail_blocked": False, "guardrail_reason": ""}
