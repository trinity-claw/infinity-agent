"""In-memory store for human-escalation sessions.

Tracks the bridge between a user's web chat session and the WhatsApp
conversation with the human operator. Lifecycle:
  1. Sentiment agent calls escalate_to_human → session created here.
  2. User's subsequent messages are forwarded to operator via WhatsApp.
  3. Operator's WhatsApp replies come through the webhook and land here.
  4. Frontend polls /v1/messages/{session_id} and renders operator messages.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EscalationMessage:
    sender: str   # "user" | "agent"
    content: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class EscalationSession:
    session_id: str
    user_id: str
    operator_number: str  # WhatsApp number that received the escalation notice
    messages: list[EscalationMessage] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    active: bool = True


class EscalationSessionStore:
    """Thread-safe-enough in-memory session store (single-process)."""

    def __init__(self) -> None:
        self._sessions: dict[str, EscalationSession] = {}
        self._user_to_session: dict[str, str] = {}       # user_id → session_id
        self._operator_to_session: dict[str, str] = {}   # normalized_number → session_id

    # ── Creation ──────────────────────────────────────────────────────────────

    def create_session(self, user_id: str, operator_number: str) -> str:
        """Create a new escalation session and return its session_id."""
        # Keep a single active handoff per user to avoid stale-session drift.
        previous_session = self.get_session_by_user(user_id)
        if previous_session and previous_session.active:
            previous_session.active = False

        session_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
        session = EscalationSession(
            session_id=session_id,
            user_id=user_id,
            operator_number=operator_number,
        )
        self._sessions[session_id] = session
        self._user_to_session[user_id] = session_id
        normalized = _normalize_number(operator_number)
        self._operator_to_session[normalized] = session_id
        return session_id

    # ── Lookup ─────────────────────────────────────────────────────────────────

    def get_session(self, session_id: str) -> Optional[EscalationSession]:
        return self._sessions.get(session_id)

    def get_session_by_user(self, user_id: str) -> Optional[EscalationSession]:
        session_id = self._user_to_session.get(user_id)
        if session_id:
            return self._sessions.get(session_id)
        return None

    def get_session_by_operator_number(self, phone: str) -> Optional[EscalationSession]:
        """Find the active session associated with an operator's phone number."""
        normalized = _normalize_number(phone)
        session_id = self._operator_to_session.get(normalized)
        if session_id:
            session = self._sessions.get(session_id)
            if session and session.active:
                return session

        # Fuzzy fallback for provider inconsistencies (country code, 9th digit, etc.).
        for session in self._sessions.values():
            if not session.active:
                continue
            if _numbers_match(normalized, _normalize_number(session.operator_number)):
                return session
        return None

    def get_active_sessions(self) -> list[EscalationSession]:
        """Return all currently active escalation sessions."""
        return [session for session in self._sessions.values() if session.active]

    # ── Messaging ──────────────────────────────────────────────────────────────

    def add_message(self, session_id: str, sender: str, content: str) -> bool:
        session = self._sessions.get(session_id)
        if not session:
            return False
        session.messages.append(EscalationMessage(sender=sender, content=content))
        return True

    def get_messages(self, session_id: str, since: int = 0) -> list[dict]:
        """Return messages starting from index `since`."""
        session = self._sessions.get(session_id)
        if not session:
            return []
        return [
            {
                "sender": m.sender,
                "content": m.content,
                "timestamp": m.timestamp,
                "index": since + i,
            }
            for i, m in enumerate(session.messages[since:])
        ]

    def close_session(self, session_id: str) -> None:
        session = self._sessions.get(session_id)
        if session:
            session.active = False


def _normalize_number(phone: str) -> str:
    """Strip non-digit characters for fuzzy phone number matching."""
    return "".join(c for c in phone if c.isdigit())


def _numbers_match(a: str, b: str) -> bool:
    """Loose phone matching using canonical suffixes."""
    if not a or not b:
        return False
    if a == b:
        return True
    # Compare last 8-11 digits to handle DDI/DDD/injected 9th digit variance.
    for size in (11, 10, 9, 8):
        if len(a) >= size and len(b) >= size and a[-size:] == b[-size:]:
            return True
    return False


# Module-level singleton used by tools and routes
session_store = EscalationSessionStore()
