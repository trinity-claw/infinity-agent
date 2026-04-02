"""Customer Support Agent node.

Handles account issues, troubleshooting, and ticket creation.
Uses tool-calling with injected repositories.
"""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage

from src.agents.prompts.support_prompt import SUPPORT_SYSTEM_PROMPT
from src.agents.state import AgentState
from src.agents.tools.support_tools import create_support_tools
from src.domain.ports.ticket_repository import TicketRepository
from src.domain.ports.user_repository import UserRepository
from src.infrastructure.llm.model_factory import get_support_llm

logger = logging.getLogger(__name__)


def create_support_node(
    user_repo: UserRepository,
    ticket_repo: TicketRepository,
):
    """Factory that creates a support node with injected repositories.

    Args:
        user_repo: Repository for user data access.
        ticket_repo: Repository for support ticket operations.

    Returns:
        An async function that serves as the LangGraph node.
    """
    tools = create_support_tools(user_repo, ticket_repo)

    async def support_node(state: AgentState) -> dict:
        """Handle customer support requests with tool-calling.

        Flow:
        1. LLM reads the conversation + system prompt
        2. Decides which tools to call (lookup_user first, then others)
        3. Executes tools and feeds results back to LLM
        4. LLM generates a personalized, empathetic response
        """
        llm = get_support_llm().bind_tools(tools)
        user_id = state.get("user_id", "unknown")

        # Inject user_id context into the system prompt
        context_prompt = (
            f"{SUPPORT_SYSTEM_PROMPT}\n\n"
            f"## Current Session\n"
            f"Current customer user_id: {user_id}\n"
            f"Always use this user_id when calling tools."
        )

        messages = [SystemMessage(content=context_prompt)] + list(
            state["messages"]
        )

        # Iterative tool-calling loop (max 3 rounds to prevent infinite loops)
        for _ in range(3):
            response = await llm.ainvoke(messages)

            if not response.tool_calls:
                break

            # Execute tool calls
            tool_map = {t.name: t for t in tools}
            tool_messages = []

            for tool_call in response.tool_calls:
                tool_fn = tool_map.get(tool_call["name"])
                if tool_fn:
                    logger.info("Support agent calling tool: %s", tool_call["name"])
                    result = await tool_fn.ainvoke(tool_call["args"])
                    tool_messages.append(
                        ToolMessage(
                            content=str(result),
                            tool_call_id=tool_call["id"],
                        )
                    )

            messages = messages + [response] + tool_messages

        return {
            "messages": [
                AIMessage(content=response.content, name="support")
            ],
        }

    return support_node
