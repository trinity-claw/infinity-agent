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
) -> list:
    """Factory that creates support tools with injected repositories.

    Args:
        user_repo: Repository for user data access.
        ticket_repo: Repository for support ticket operations.

    Returns:
        List of LangChain tools bound to the provided repositories.
    """

    @tool
    async def lookup_user(user_id: str) -> str:
        """Look up a customer's account information.

        Use this tool FIRST when handling any support request to get
        the customer's profile, plan, and account status.

        Args:
            user_id: The customer's user ID.
        """
        user = await user_repo.find_by_id(user_id)
        if not user:
            return f"No customer found with ID: {user_id}. This user may not have an account."
        return user.to_summary()

    @tool
    async def get_transaction_history(user_id: str) -> str:
        """Get the customer's recent transaction history.

        Use this to investigate missing money, failed transactions,
        or to verify payment status.

        Args:
            user_id: The customer's user ID.
        """
        transactions = await user_repo.get_transaction_history(user_id, limit=10)
        if not transactions:
            return f"No transactions found for user {user_id}."

        lines = [f"Recent transactions for {user_id}:"]
        for tx in transactions:
            lines.append(f"  • {tx.to_summary()}")
        return "\n".join(lines)

    @tool
    async def create_support_ticket(
        user_id: str, issue: str, priority: str = "medium"
    ) -> str:
        """Create a support ticket for issues that need follow-up.

        Use this when the issue cannot be resolved immediately and
        needs to be tracked by the support team.

        Args:
            user_id: The customer's user ID.
            issue: Description of the issue.
            priority: Ticket priority — 'low', 'medium', 'high', or 'urgent'.
        """
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
            f"Support ticket created successfully!\n{ticket.to_summary()}\n"
            f"Our team will review this within 24 hours."
        )

    @tool
    async def check_service_status() -> str:
        """Check the operational status of InfinitePay services.

        Use this when a customer reports issues that might be caused
        by a service outage or degradation.
        """
        # Simulated service status
        services = {
            "Maquininha Smart": ServiceStatus.OPERATIONAL,
            "InfiniteTap": ServiceStatus.OPERATIONAL,
            "Pix": ServiceStatus.OPERATIONAL,
            "Link de Pagamento": ServiceStatus.OPERATIONAL,
            "Conta Digital": ServiceStatus.OPERATIONAL,
            "Cartão Virtual": ServiceStatus.OPERATIONAL,
            "Transferências": ServiceStatus.OPERATIONAL,
        }

        lines = ["InfinitePay Service Status:"]
        for service, status in services.items():
            emoji = "✅" if status == ServiceStatus.OPERATIONAL else "⚠️"
            lines.append(f"  {emoji} {service}: {status.value}")
        return "\n".join(lines)

    @tool
    async def reset_password_request(user_id: str) -> str:
        """Initiate a password reset for the customer's account.

        Use this when the customer cannot sign in to their account
        and needs to reset their password.

        Args:
            user_id: The customer's user ID.
        """
        user = await user_repo.find_by_id(user_id)
        if not user:
            return f"Cannot initiate password reset: user {user_id} not found."

        return (
            f"Password reset initiated for {user.name}.\n"
            f"A reset link has been sent to {user.email}.\n"
            f"The link will expire in 30 minutes."
        )

    @tool
    async def get_account_balance(user_id: str) -> str:
        """Check the customer's account balance.

        Args:
            user_id: The customer's user ID.
        """
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
