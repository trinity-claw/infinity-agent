"""Helpers for consistent LangGraph checkpointer configuration."""

from __future__ import annotations

import re


def sanitize_identifier(value: str | None, fallback: str) -> str:
    """Normalize IDs used by LangGraph configurable keys."""
    normalized = (value or "").strip().lower()
    if not normalized:
        return fallback

    normalized = re.sub(r"[^a-z0-9._:-]", "_", normalized)
    normalized = normalized.strip("._:-")
    if not normalized:
        return fallback

    return normalized[:100]


def build_swarm_config(
    thread_id: str | None,
    checkpoint_ns: str,
    *,
    fallback_thread_id: str = "client_web",
) -> dict[str, dict[str, str]]:
    """Build a safe runnable config for LangGraph checkpointers."""
    safe_thread_id = sanitize_identifier(thread_id, fallback=fallback_thread_id)
    safe_checkpoint_ns = sanitize_identifier(checkpoint_ns, fallback="chat")
    return {
        "configurable": {
            "thread_id": safe_thread_id,
            "checkpoint_ns": safe_checkpoint_ns,
        }
    }
