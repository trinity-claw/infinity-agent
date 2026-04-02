"""Domain exceptions.

Centralized exception hierarchy for the application.
All exceptions inherit from InfinityAgentError for clean error handling.
"""


class InfinityAgentError(Exception):
    """Base exception for the Infinity Agent application."""


class GuardrailBlockedError(InfinityAgentError):
    """Raised when user input or agent output is blocked by guardrails."""

    def __init__(self, reason: str, category: str = "blocked"):
        self.reason = reason
        self.category = category
        super().__init__(f"Guardrail blocked: {reason}")


class AgentRoutingError(InfinityAgentError):
    """Raised when the router cannot determine the appropriate agent."""

    def __init__(self, message: str, intent: str | None = None):
        self.intent = intent
        super().__init__(f"Routing error: {message}")


class KnowledgeRetrievalError(InfinityAgentError):
    """Raised when RAG retrieval fails."""


class UserNotFoundError(InfinityAgentError):
    """Raised when a user_id doesn't exist in the system."""

    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"User not found: {user_id}")


class ConfigurationError(InfinityAgentError):
    """Raised when required configuration is missing or invalid."""
