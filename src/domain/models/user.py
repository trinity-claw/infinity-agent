"""Domain model for user entities.

Represents an InfinitePay customer with account details.
Used by the Customer Support Agent to provide personalized support.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class User:
    """InfinitePay customer entity."""

    user_id: str
    name: str
    email: str
    phone: str
    document: str  # CPF or CNPJ
    account_type: str  # "PF" or "PJ"
    plan: str  # e.g., "InfiniteTap", "Maquininha Smart"
    balance: float = 0.0
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_summary(self) -> str:
        """Human-readable summary for the support agent."""
        status = "Ativa" if self.is_active else "Inativa"
        return (
            f"Cliente: {self.name}\n"
            f"Email: {self.email}\n"
            f"Telefone: {self.phone}\n"
            f"Documento: {self.document}\n"
            f"Tipo de Conta: {self.account_type}\n"
            f"Plano: {self.plan}\n"
            f"Saldo: R$ {self.balance:,.2f}\n"
            f"Status: {status}\n"
            f"Cliente desde: {self.created_at.strftime('%d/%m/%Y')}"
        )


@dataclass
class Transaction:
    """A financial transaction on the user's account."""

    transaction_id: str
    user_id: str
    amount: float
    transaction_type: str  # "credit", "debit", "pix", "transfer"
    description: str
    status: str  # "completed", "pending", "failed"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_summary(self) -> str:
        """Human-readable transaction summary."""
        sign = "+" if self.amount >= 0 else ""
        return (
            f"[{self.created_at.strftime('%d/%m %H:%M')}] "
            f"{self.transaction_type.upper()} — "
            f"{sign}R$ {abs(self.amount):,.2f} — "
            f"{self.description} ({self.status})"
        )
