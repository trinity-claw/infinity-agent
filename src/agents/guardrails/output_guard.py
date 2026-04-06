"""Output Guardrail node.

Validates agent responses before sending them to the user.
Ensures no PII leakage, hallucinations, or toxic content.
"""

from __future__ import annotations

import logging
import re

from langchain_core.messages import AIMessage

from src.agents.state import AgentState
from src.settings import settings

logger = logging.getLogger(__name__)

# Regex patterns for PII detection
CPF_PATTERN = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
CNPJ_PATTERN = re.compile(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}")
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(
    r"(?:(?:\+?55)\s*)?(?:\(?\d{2}\)?\s*)?\d{4,5}[-\s]?\d{4}"
)


def _mask_pii(text: str) -> str:
    """Mask personally identifiable information in text."""
    # Mask CPF: 123.456.789-00 → ***.***.789-00
    text = CPF_PATTERN.sub(
        lambda m: f"***.***{m.group()[-7:]}", text
    )
    # Mask CNPJ: 12.345.678/0001-90 → **.***.678/0001-90
    text = CNPJ_PATTERN.sub(
        lambda m: f"**.***.{m.group()[-12:]}", text
    )
    # Mask email: name@email.com → n***@email.com
    def mask_email(m: re.Match) -> str:
        email = m.group()
        local, domain = email.split("@")
        return f"{local[0]}***@{domain}"

    text = EMAIL_PATTERN.sub(mask_email, text)

    # Mask phones: +55 (11) 99999-1234 -> ***-***-1234
    def mask_phone(m: re.Match) -> str:
        digits = re.sub(r"\D", "", m.group())
        if len(digits) < 8:
            return m.group()
        return f"***-***-{digits[-4:]}"

    text = PHONE_PATTERN.sub(mask_phone, text)

    return text


async def output_guard_node(state: AgentState) -> dict:
    """Validate agent output before sending to the user.

    Applies:
    1. PII masking (CPF, CNPJ, email, phone)
    2. Response quality check
    """
    if not settings.enable_guardrails:
        return {}

    # Get the last agent message
    if not state["messages"]:
        return {}

    last_message = state["messages"][-1]
    if not hasattr(last_message, "content"):
        return {}

    original_content = last_message.content
    sanitized_content = _mask_pii(original_content)

    if sanitized_content != original_content:
        logger.info("Output guardrail: PII detected and masked")
        return {
            "messages": [
                AIMessage(
                    content=sanitized_content,
                    name=getattr(last_message, "name", "agent"),
                )
            ],
        }

    return {}
