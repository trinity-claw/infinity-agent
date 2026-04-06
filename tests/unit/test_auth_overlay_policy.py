"""Regression checks for frontend Google auth allow rules."""

from __future__ import annotations

from pathlib import Path


AUTH_OVERLAY_PATH = Path("frontend-react/src/components/AuthOverlay.jsx")
FRONTEND_ENV_EXAMPLE_PATH = Path("frontend-react/.env.example")


def test_auth_overlay_uses_token_based_allow_policy() -> None:
    """Auth overlay should support token-based allow checks for evaluator access."""
    content = AUTH_OVERLAY_PATH.read_text(encoding="utf-8")
    assert "VITE_ALLOWED_EMAIL_CONTAINS" in content
    assert "allowedEmailContainsTokens" in content
    assert "isEmailAllowed" in content


def test_frontend_env_example_includes_token_policy_variable() -> None:
    """Frontend env example should document the token-based allow variable."""
    content = FRONTEND_ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
    assert "VITE_ALLOWED_EMAIL_CONTAINS=" in content
