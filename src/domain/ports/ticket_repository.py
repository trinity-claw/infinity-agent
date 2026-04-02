"""Port: Ticket Repository interface.

Defines the contract for support ticket operations.
"""

from abc import ABC, abstractmethod

from src.domain.models.enums import TicketPriority
from src.domain.models.ticket import SupportTicket


class TicketRepository(ABC):
    """Abstract interface for support ticket operations."""

    @abstractmethod
    async def create(
        self,
        user_id: str,
        issue: str,
        priority: TicketPriority = TicketPriority.MEDIUM,
    ) -> SupportTicket:
        """Create a new support ticket."""
        ...

    @abstractmethod
    async def find_by_id(self, ticket_id: str) -> SupportTicket | None:
        """Retrieve a ticket by its ID."""
        ...

    @abstractmethod
    async def find_by_user(self, user_id: str) -> list[SupportTicket]:
        """Retrieve all tickets for a specific user."""
        ...

    @abstractmethod
    async def update_status(
        self, ticket_id: str, status: str, resolution: str | None = None
    ) -> SupportTicket | None:
        """Update ticket status and optional resolution."""
        ...
