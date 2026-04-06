"""Unit tests for support-tool user isolation."""

from __future__ import annotations

import pytest

from src.agents.tools.support_tools import create_support_tools


class _DummyUser:
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        self.name = "Cliente Teste"
        self.email = "cliente@test.com"

    def to_summary(self) -> str:
        return f"User<{self.user_id}>"


class _DummyTransaction:
    def to_summary(self) -> str:
        return "tx-001: R$ 10,00"


class _DummyTicket:
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id

    def to_summary(self) -> str:
        return f"Ticket for {self.user_id}"


class _StubUserRepo:
    def __init__(self) -> None:
        self.lookup_ids: list[str] = []
        self.tx_ids: list[str] = []
        self.balance_ids: list[str] = []

    async def find_by_id(self, user_id: str):
        self.lookup_ids.append(user_id)
        return _DummyUser(user_id)

    async def get_transaction_history(self, user_id: str, limit: int = 10):
        self.tx_ids.append(user_id)
        return [_DummyTransaction()]

    async def get_account_balance(self, user_id: str):
        self.balance_ids.append(user_id)
        return 1240.35


class _StubTicketRepo:
    def __init__(self) -> None:
        self.created_for: list[str] = []

    async def create(self, user_id: str, issue: str, priority):
        self.created_for.append(user_id)
        return _DummyTicket(user_id)


@pytest.mark.asyncio
async def test_support_tools_are_scoped_to_bound_user() -> None:
    user_repo = _StubUserRepo()
    ticket_repo = _StubTicketRepo()

    tools = create_support_tools(
        user_repo=user_repo,
        ticket_repo=ticket_repo,
        bound_user_id="client_current",
    )
    tool_map = {tool.name: tool for tool in tools}

    for tool_name in (
        "lookup_user",
        "get_transaction_history",
        "create_support_ticket",
        "reset_password_request",
        "get_account_balance",
    ):
        assert "user_id" not in tool_map[tool_name].args

    await tool_map["lookup_user"].ainvoke({})
    await tool_map["get_transaction_history"].ainvoke({})
    await tool_map["get_account_balance"].ainvoke({})
    await tool_map["reset_password_request"].ainvoke({})
    await tool_map["create_support_ticket"].ainvoke({"issue": "Teste"})

    assert user_repo.lookup_ids == ["client_current", "client_current"]
    assert user_repo.tx_ids == ["client_current"]
    assert user_repo.balance_ids == ["client_current"]
    assert ticket_repo.created_for == ["client_current"]
