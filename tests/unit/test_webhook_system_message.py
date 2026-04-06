"""Unit tests for webhook system-message detection."""

from __future__ import annotations

from src.api.v1.routes.webhook import _is_operator_system_message


def test_system_message_detects_escalation_templates() -> None:
    assert _is_operator_system_message("🚨 *ESCALAMENTO — InfinitePay AI*")
    assert _is_operator_system_message("Sessão: ESC-1234ABCD")
    assert _is_operator_system_message("*[User 5511999999999]:* teste")


def test_system_message_allows_real_operator_replies() -> None:
    assert not _is_operator_system_message("easw")
    assert not _is_operator_system_message("Como posso ajudar você?")

