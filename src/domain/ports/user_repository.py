"""Port: User Repository interface.

Defines the contract for accessing user data.
The Infrastructure layer provides the concrete implementation.
"""

from abc import ABC, abstractmethod

from src.domain.models.user import Transaction, User


class UserRepository(ABC):
    """Abstract interface for user data access."""

    @abstractmethod
    async def find_by_id(self, user_id: str) -> User | None:
        """Retrieve a user by their ID."""
        ...

    @abstractmethod
    async def find_by_email(self, email: str) -> User | None:
        """Retrieve a user by their email address."""
        ...

    @abstractmethod
    async def get_transaction_history(
        self, user_id: str, limit: int = 10
    ) -> list[Transaction]:
        """Retrieve recent transactions for a user."""
        ...

    @abstractmethod
    async def get_account_balance(self, user_id: str) -> float | None:
        """Retrieve the current account balance for a user."""
        ...
