"""API request/response schemas.

Pydantic models for the REST API. These stay in the Presentation layer
and are NOT used inside the domain or agent layers.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming chat request."""

    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    user_id: str = Field(..., min_length=1, max_length=100, description="User identifier")
    user_name: Optional[str] = Field(
        default=None,
        max_length=120,
        description="Authenticated user display name from Google Sign-In.",
    )
    user_email: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Authenticated user email from Google Sign-In.",
    )
    session_id: Optional[str] = Field(
        default=None,
        description=(
            "Active escalation session ID. If provided, message is forwarded "
            "to the human operator instead of the AI swarm."
        ),
    )
    session_token: Optional[str] = Field(
        default=None,
        description=(
            "Escalation session token required when sending messages to an active "
            "human handoff session."
        ),
    )


class ChatResponse(BaseModel):
    """Chat response returned to the client."""

    response: str = Field(..., description="Agent response text")
    agent_used: str = Field(..., description="Which agent processed the request")
    intent: str = Field(default="", description="Classified user intent")
    language: str = Field(default="pt-BR", description="Detected language")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "1.0.0"
    services: dict[str, str] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    detail: str = ""
    status_code: int = 500
