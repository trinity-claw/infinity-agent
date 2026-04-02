"""Domain model for support tickets.

Represents a customer support case created by the Support Agent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.domain.models.enums import TicketPriority, TicketStatus


@dataclass
class SupportTicket:
    """A customer support ticket."""

    ticket_id: str
    user_id: str
    issue: str
    priority: TicketPriority = TicketPriority.MEDIUM
    status: TicketStatus = TicketStatus.OPEN
    assigned_to: str | None = None
    resolution: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_summary(self) -> str:
        """Human-readable ticket summary."""
        return (
            f"Ticket #{self.ticket_id}\n"
            f"Issue: {self.issue}\n"
            f"Priority: {self.priority.value}\n"
            f"Status: {self.status.value}\n"
            f"Created: {self.created_at.strftime('%d/%m/%Y %H:%M')}"
        )
