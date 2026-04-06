"""Shared routing and overlap detection rules for agent nodes."""

from __future__ import annotations

import re

_OPERATIONAL_SUPPORT_PATTERNS = (
    r"\bstatus\b.{0,25}\bservic",
    r"\bservice status\b",
    r"\b(outage|downtime|instab|indispon|fora do ar|is down)\b",
    r"\b(infinitepay|service|servico|servicos)\b.{0,20}\bdown\b",
    r"\binstabilidade\b",
    r"\bservic[oos].{0,25}\b(indisponivel|instavel|fora do ar)\b",
    r"\bpix\b.{0,20}\b(instabilidade|fora do ar|indisponivel)\b",
)

_SUPPORT_ACCOUNT_PATTERNS = (
    r"\bnao consigo\b.{0,30}\b(acessar|entrar|transferir|pagar)\b",
    r"\bi can't\b.{0,30}\b(sign in|login|transfer|pay)\b",
)

_OPERATIONAL_SUPPORT_REGEX = tuple(
    re.compile(pattern)
    for pattern in _OPERATIONAL_SUPPORT_PATTERNS
)
_SUPPORT_OVERLAP_REGEX = tuple(
    re.compile(pattern)
    for pattern in (*_OPERATIONAL_SUPPORT_PATTERNS, *_SUPPORT_ACCOUNT_PATTERNS)
)


def is_operational_support_query(message: str) -> bool:
    """Detect service-status and outage queries that must route to support."""
    if not message:
        return False
    text = message.lower()
    return any(regex.search(text) for regex in _OPERATIONAL_SUPPORT_REGEX)


def is_support_overlap_query(message: str) -> bool:
    """Detect support-style operational/account issues misrouted to knowledge."""
    if not message:
        return False
    text = message.lower()
    return any(regex.search(text) for regex in _SUPPORT_OVERLAP_REGEX)
