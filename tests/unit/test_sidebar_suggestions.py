"""Unit tests for curated quick suggestions in the React sidebar."""

from __future__ import annotations

from pathlib import Path


SIDEBAR_PATH = Path("frontend-react/src/components/Sidebar.jsx")


def test_sidebar_exists() -> None:
    """Sidebar component should exist in expected path."""
    assert SIDEBAR_PATH.exists()


def test_removed_unsupported_service_status_suggestion() -> None:
    """The unsupported service-status quick suggestion should not be present."""
    content = SIDEBAR_PATH.read_text(encoding="utf-8")
    assert "Status dos servicos" not in content
    assert "Status dos serviços" not in content
    assert "status atual dos servicos da InfinitePay" not in content
    assert "status atual dos serviços da InfinitePay" not in content


def test_curated_quick_suggestions_still_include_handoff() -> None:
    """Curated list should still include meaningful support handoff shortcut."""
    content = SIDEBAR_PATH.read_text(encoding="utf-8")
    assert "Falar com atendente humano" in content
    assert "Quero falar com um atendente humano" in content


def test_sidebar_default_user_is_valid_mock_profile() -> None:
    """Default mock user should map to seeded support data for evaluator UX."""
    content = SIDEBAR_PATH.read_text(encoding="utf-8")
    assert "const getFallbackUserId = () => 'client789';" in content


def test_sidebar_uses_dropdown_suggestion_groups() -> None:
    """Suggestion UI should include grouped dropdown behavior."""
    content = SIDEBAR_PATH.read_text(encoding="utf-8")
    assert "SUGGESTION_GROUPS" in content
    assert "suggestionGroupSelect" in content
    assert "Sugestões guiadas" in content
    assert "setSelectedSuggestionGroup" in content
    assert "suggestions-dropdown-trigger" in content
