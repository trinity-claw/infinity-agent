"""Customer Support Agent tools.

Tools for user lookup, transaction history, ticket management, and account operations.
All tools receive repository dependencies via factory injection.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.tools import tool

from src.domain.models.enums import ServiceStatus, TicketPriority

if TYPE_CHECKING:
    from src.domain.ports.ticket_repository import TicketRepository
    from src.domain.ports.user_repository import UserRepository


def create_support_tools(
    user_repo: UserRepository,
    ticket_repo: TicketRepository,
    *,
    bound_user_id: str,
) -> list:
    """Factory that creates support tools with injected repositories."""

    def _current_user_id() -> str:
        return bound_user_id

    @tool
    async def lookup_user() -> str:
        """Look up a customer's account information."""
        user_id = _current_user_id()
        user = await user_repo.find_by_id(user_id)
        if not user:
            return f"No customer found with ID: {user_id}. This user may not have an account."
        return user.to_summary()

    @tool
    async def get_transaction_history() -> str:
        """Get the customer's recent transaction history."""
        user_id = _current_user_id()
        transactions = await user_repo.get_transaction_history(user_id, limit=10)
        if not transactions:
            return f"No transactions found for user {user_id}."

        lines = [f"Recent transactions for {user_id}:"]
        for tx in transactions:
            lines.append(f"  - {tx.to_summary()}")
        return "\n".join(lines)

    @tool
    async def create_support_ticket(issue: str, priority: str = "medium") -> str:
        """Create a support ticket for issues requiring follow-up."""
        user_id = _current_user_id()
        try:
            ticket_priority = TicketPriority(priority.lower())
        except ValueError:
            ticket_priority = TicketPriority.MEDIUM

        ticket = await ticket_repo.create(
            user_id=user_id,
            issue=issue,
            priority=ticket_priority,
        )
        return (
            f"Support ticket created successfully.\n{ticket.to_summary()}\n"
            f"Our team will review this within 24 hours."
        )

    @tool
    async def check_service_status() -> str:
        """Check the operational status of InfinitePay services."""
        services = {
            "Maquininha Smart": ServiceStatus.OPERATIONAL,
            "InfiniteTap": ServiceStatus.OPERATIONAL,
            "Pix": ServiceStatus.OPERATIONAL,
            "Link de Pagamento": ServiceStatus.OPERATIONAL,
            "Conta Digital": ServiceStatus.OPERATIONAL,
            "Cartao Virtual": ServiceStatus.OPERATIONAL,
            "Transferencias": ServiceStatus.OPERATIONAL,
        }

        lines = ["InfinitePay Service Status:"]
        for service, status in services.items():
            icon = "[OK]" if status == ServiceStatus.OPERATIONAL else "[WARN]"
            lines.append(f"  {icon} {service}: {status.value}")
        return "\n".join(lines)

    @tool
    async def reset_password_request() -> str:
        """Initiate a password reset for the customer account."""
        user_id = _current_user_id()
        user = await user_repo.find_by_id(user_id)
        if not user:
            return f"Cannot initiate password reset: user {user_id} not found."

        return (
            f"Password reset initiated for {user.name}.\n"
            f"A reset link was sent to {user.email}.\n"
            f"The link expires in 30 minutes."
        )

    @tool
    async def get_account_balance() -> str:
        """Check the customer's account balance."""
        user_id = _current_user_id()
        balance = await user_repo.get_account_balance(user_id)
        if balance is None:
            return f"Could not retrieve balance for user {user_id}."
        return f"Current account balance: R$ {balance:,.2f}"

    return [
        lookup_user,
        get_transaction_history,
        create_support_ticket,
        check_service_status,
        reset_password_request,
        get_account_balance,
    ]
