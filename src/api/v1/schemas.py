"""API request/response schemas.

Pydantic models for the REST API. These stay in the Presentation layer
and are NOT used inside the domain or agent layers.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming chat request — matches the challenge specification."""

    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    user_id: str = Field(..., min_length=1, max_length=100, description="User identifier")


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
