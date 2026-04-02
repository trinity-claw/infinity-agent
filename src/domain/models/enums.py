"""Domain enumerations for the agent swarm.

These enums define the bounded vocabulary of the domain.
Every classification, category, or status should be an enum—never a raw string.
"""

from enum import StrEnum


class Intent(StrEnum):
    """User message intent categories, as classified by the Router Agent."""

    KNOWLEDGE = "knowledge"
    SUPPORT = "support"
    GENERAL = "general"
    ESCALATION = "escalation"


class AgentType(StrEnum):
    """Identifiers for each agent in the swarm."""

    ROUTER = "router"
    KNOWLEDGE = "knowledge"
    SUPPORT = "support"
    SENTIMENT = "sentiment"


class SentimentLevel(StrEnum):
    """User sentiment classification levels."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    FRUSTRATED = "frustrated"


class UrgencyLevel(StrEnum):
    """Urgency classification for support requests."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketStatus(StrEnum):
    """Support ticket lifecycle states."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class TicketPriority(StrEnum):
    """Support ticket priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class GuardrailAction(StrEnum):
    """Actions that guardrails can take on a message."""

    ALLOW = "allow"
    BLOCK = "block"
    WARN = "warn"


class ServiceStatus(StrEnum):
    """InfinitePay service operational statuses."""

    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    OUTAGE = "outage"
    MAINTENANCE = "maintenance"
