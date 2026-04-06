"""Unit tests for WhatsApp escalation session store."""

from __future__ import annotations

from src.infrastructure.whatsapp.session_store import EscalationSessionStore


def test_create_session_replaces_previous_active_session_for_same_user() -> None:
    store = EscalationSessionStore()
    first = store.create_session(user_id="client_1", operator_number="5511999999999")
    second = store.create_session(user_id="client_1", operator_number="5511999999999")

    first_session = store.get_session(first)
    second_session = store.get_session(second)
    assert first_session is not None and first_session.active is False
    assert second_session is not None and second_session.active is True
    assert store.get_session_by_user("client_1") is second_session


def test_get_session_by_operator_number_matches_fuzzy_number_formats() -> None:
    store = EscalationSessionStore()
    session_id = store.create_session(user_id="client_2", operator_number="+55 (11) 99999-9999")

    by_full = store.get_session_by_operator_number("5511999999999")
    by_short = store.get_session_by_operator_number("11999999999")
    by_jid_like = store.get_session_by_operator_number("55 11 99999-9999")

    assert by_full is not None and by_full.session_id == session_id
    assert by_short is not None and by_short.session_id == session_id
    assert by_jid_like is not None and by_jid_like.session_id == session_id


def test_get_session_by_operator_number_matches_incomplete_operator_number() -> None:
    store = EscalationSessionStore()
    session_id = store.create_session(user_id="client_3", operator_number="551199979406")
    by_complete = store.get_session_by_operator_number("5511999794061")
    assert by_complete is not None and by_complete.session_id == session_id


def test_validate_session_token() -> None:
    store = EscalationSessionStore()
    session_id = store.create_session(user_id="client_4", operator_number="5511999794061")
    session = store.get_session(session_id)
    assert session is not None

    assert store.validate_session_token(session_id, session.session_token) is True
    assert store.validate_session_token(session_id, "invalid") is False
    assert store.validate_session_token(session_id, None) is False
