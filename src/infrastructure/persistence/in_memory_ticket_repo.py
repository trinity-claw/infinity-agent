"""In-memory Ticket Repository implementation.

Provides a simulated ticket system for the Customer Support Agent.
"""

import uuid
from datetime import datetime, timezone

from src.domain.models.enums import TicketPriority, TicketStatus
from src.domain.models.ticket import SupportTicket
from src.domain.ports.ticket_repository import TicketRepository


class InMemoryTicketRepository(TicketRepository):
    """In-memory implementation of TicketRepository."""

    def __init__(self) -> None:
        self._tickets: dict[str, SupportTicket] = {}

    async def create(
        self,
        user_id: str,
        issue: str,
        priority: TicketPriority = TicketPriority.MEDIUM,
    ) -> SupportTicket:
        ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        ticket = SupportTicket(
            ticket_id=ticket_id,
            user_id=user_id,
            issue=issue,
            priority=priority,
            status=TicketStatus.OPEN,
        )
        self._tickets[ticket_id] = ticket
        return ticket

    async def find_by_id(self, ticket_id: str) -> SupportTicket | None:
        return self._tickets.get(ticket_id)

    async def find_by_user(self, user_id: str) -> list[SupportTicket]:
        return [t for t in self._tickets.values() if t.user_id == user_id]

    async def update_status(
        self, ticket_id: str, status: str, resolution: str | None = None
    ) -> SupportTicket | None:
        ticket = self._tickets.get(ticket_id)
        if ticket:
            ticket.status = TicketStatus(status)
            ticket.resolution = resolution
            ticket.updated_at = datetime.now(timezone.utc)
        return ticket
