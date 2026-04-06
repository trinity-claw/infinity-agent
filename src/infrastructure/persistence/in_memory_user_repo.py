"""In-memory User Repository implementation.

Provides a simulated customer database for challenge/demo scenarios.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.domain.models.user import Transaction, User
from src.domain.ports.user_repository import UserRepository


def _seed_users() -> dict[str, User]:
    """Generate realistic fake InfinitePay customers."""
    now = datetime.now(timezone.utc)
    return {
        "client789": User(
            user_id="client789",
            name="Maria Silva Santos",
            email="maria.santos@email.com",
            phone="(11) 98765-4321",
            document="123.456.789-00",
            account_type="PF",
            plan="InfiniteTap",
            balance=3_450.75,
            is_active=True,
            created_at=now - timedelta(days=180),
        ),
        "client001": User(
            user_id="client001",
            name="Joao Pedro Oliveira",
            email="joao.oliveira@empresa.com",
            phone="(21) 99876-5432",
            document="12.345.678/0001-90",
            account_type="PJ",
            plan="Maquininha Smart",
            balance=15_230.00,
            is_active=True,
            created_at=now - timedelta(days=365),
        ),
        "client002": User(
            user_id="client002",
            name="Ana Carolina Ferreira",
            email="ana.ferreira@loja.com",
            phone="(31) 97654-3210",
            document="98.765.432/0001-10",
            account_type="PJ",
            plan="Maquininha Smart",
            balance=42_100.50,
            is_active=True,
            created_at=now - timedelta(days=540),
            metadata={"faturamento_mensal": "R$ 45.000"},
        ),
        "client003": User(
            user_id="client003",
            name="Carlos Eduardo Lima",
            email="carlos.lima@gmail.com",
            phone="(41) 96543-2109",
            document="987.654.321-00",
            account_type="PF",
            plan="InfiniteTap",
            balance=890.25,
            is_active=False,
            created_at=now - timedelta(days=90),
            metadata={"blocked_reason": "Documentacao pendente"},
        ),
        "client004": User(
            user_id="client004",
            name="Fernanda Costa Almeida",
            email="fernanda@studio.com",
            phone="(51) 95432-1098",
            document="45.678.901/0001-23",
            account_type="PJ",
            plan="Link de Pagamento",
            balance=8_750.00,
            is_active=True,
            created_at=now - timedelta(days=270),
        ),
        "client_pelissarog_gmail_com": User(
            user_id="client_pelissarog_gmail_com",
            name="Gustavo Pelissaro",
            email="pelissarog@gmail.com",
            phone="(11) 99794-0610",
            document="111.222.333-44",
            account_type="PF",
            plan="InfiniteTap",
            balance=1_240.35,
            is_active=True,
            created_at=now - timedelta(days=120),
        ),
        "client_pelissarog_gmail.com": User(
            user_id="client_pelissarog_gmail.com",
            name="Gustavo Pelissaro",
            email="pelissarog@gmail.com",
            phone="(11) 99794-0610",
            document="111.222.333-44",
            account_type="PF",
            plan="InfiniteTap",
            balance=1_240.35,
            is_active=True,
            created_at=now - timedelta(days=120),
        ),
        "client_peli": User(
            user_id="client_peli",
            name="Gustavo Pelissaro",
            email="pelissarog@gmail.com",
            phone="(11) 99794-0610",
            document="111.222.333-44",
            account_type="PF",
            plan="InfiniteTap",
            balance=1_240.35,
            is_active=True,
            created_at=now - timedelta(days=120),
        ),
    }


def _seed_transactions() -> dict[str, list[Transaction]]:
    """Generate realistic transaction histories."""
    now = datetime.now(timezone.utc)
    return {
        "client789": [
            Transaction("tx001", "client789", 150.00, "credit", "Venda cartao credito 1x", "completed", now - timedelta(hours=2)),
            Transaction("tx002", "client789", -50.00, "pix", "Transferencia Pix", "completed", now - timedelta(hours=5)),
            Transaction("tx003", "client789", 320.00, "credit", "Venda cartao credito 3x", "completed", now - timedelta(days=1)),
            Transaction("tx004", "client789", 75.00, "debit", "Venda cartao debito", "completed", now - timedelta(days=1)),
            Transaction("tx005", "client789", -200.00, "transfer", "Transferencia bancaria", "completed", now - timedelta(days=2)),
        ],
        "client001": [
            Transaction("tx010", "client001", 1_200.00, "credit", "Venda Maquininha 12x", "completed", now - timedelta(hours=1)),
            Transaction("tx011", "client001", 450.00, "pix", "Recebimento Pix", "completed", now - timedelta(hours=3)),
            Transaction("tx012", "client001", -3_500.00, "transfer", "Pagamento fornecedor", "completed", now - timedelta(days=1)),
            Transaction("tx013", "client001", 890.00, "credit", "Venda Maquininha 6x", "completed", now - timedelta(days=2)),
        ],
        "client002": [
            Transaction("tx020", "client002", 5_600.00, "credit", "Venda Link Pagamento 12x", "completed", now - timedelta(hours=4)),
            Transaction("tx021", "client002", 2_300.00, "pix", "Recebimento Pix cliente", "completed", now - timedelta(days=1)),
            Transaction("tx022", "client002", -8_000.00, "transfer", "Pagamento salarios", "pending", now - timedelta(hours=1)),
        ],
        "client003": [
            Transaction("tx030", "client003", 95.00, "debit", "Venda debito", "completed", now - timedelta(days=5)),
            Transaction("tx031", "client003", -100.00, "pix", "Transferencia Pix", "failed", now - timedelta(days=1)),
        ],
        "client004": [
            Transaction("tx040", "client004", 750.00, "credit", "Venda Link Pagamento 3x", "completed", now - timedelta(hours=6)),
            Transaction("tx041", "client004", 400.00, "pix", "Recebimento Pix", "completed", now - timedelta(days=1)),
        ],
        "client_pelissarog_gmail_com": [
            Transaction("tx050", "client_pelissarog_gmail_com", 180.00, "credit", "Venda cartao credito", "completed", now - timedelta(hours=3)),
            Transaction("tx051", "client_pelissarog_gmail_com", -42.50, "pix", "Transferencia Pix", "completed", now - timedelta(hours=5)),
        ],
        "client_pelissarog_gmail.com": [
            Transaction("tx052", "client_pelissarog_gmail.com", 90.00, "debit", "Venda debito", "completed", now - timedelta(days=1)),
        ],
        "client_peli": [
            Transaction("tx053", "client_peli", 120.00, "credit", "Venda cartao credito", "completed", now - timedelta(days=2)),
        ],
    }


class InMemoryUserRepository(UserRepository):
    """In-memory implementation of UserRepository with pre-seeded data."""

    def __init__(self) -> None:
        self._users = _seed_users()
        self._transactions = _seed_transactions()

    async def find_by_id(self, user_id: str) -> User | None:
        direct = self._users.get(user_id)
        if direct:
            return direct

        normalized_target = _normalize_identifier(user_id)
        for key, user in self._users.items():
            if _normalize_identifier(key) == normalized_target:
                return user
        return None

    async def find_by_email(self, email: str) -> User | None:
        for user in self._users.values():
            if user.email.lower() == email.lower():
                return user
        return None

    async def get_transaction_history(
        self, user_id: str, limit: int = 10
    ) -> list[Transaction]:
        transactions = self._transactions.get(user_id, [])
        return sorted(transactions, key=lambda t: t.created_at, reverse=True)[:limit]

    async def get_account_balance(self, user_id: str) -> float | None:
        user = self._users.get(user_id)
        return user.balance if user else None


def _normalize_identifier(value: str) -> str:
    return "".join(char for char in (value or "").lower() if char.isalnum())
