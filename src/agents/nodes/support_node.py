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
    def _filter_tool_args(tool_fn, raw_args: dict | None) -> dict:
        if not isinstance(raw_args, dict):
            return {}
        allowed_keys = set(getattr(tool_fn, "args", {}).keys())
        if not allowed_keys:
            return {}
        filtered = {key: value for key, value in raw_args.items() if key in allowed_keys}
        dropped = set(raw_args.keys()) - set(filtered.keys())
        if dropped:
            logger.warning(
                "Support tool '%s' received unexpected args and ignored them: %s",
                getattr(tool_fn, "name", "unknown"),
                sorted(dropped),
            )
        return filtered

    async def support_node(state: AgentState) -> dict:
        """Handle customer support requests with tool-calling.

        Flow:
        1. LLM reads the conversation + system prompt
        2. Decides which tools to call (lookup_user first, then others)
        3. Executes tools and feeds results back to LLM
        4. LLM generates a personalized, empathetic response
        """
        user_id = state.get("user_id", "unknown")
        tools = create_support_tools(
            user_repo,
            ticket_repo,
            bound_user_id=user_id,
        )
        llm = get_support_llm().bind_tools(tools)
        authenticated_user = state.get("metadata", {}).get("authenticated_user", {})
        auth_name = authenticated_user.get("name", "")
        auth_email = authenticated_user.get("email", "")

        profile_lines = []
        if auth_name:
            profile_lines.append(f"- Authenticated name: {auth_name}")
        if auth_email:
            profile_lines.append(f"- Authenticated email: {auth_email}")

        profile_block = "\n".join(profile_lines) if profile_lines else "- No authenticated profile provided."

        # Inject session context into the system prompt
        context_prompt = (
            f"{SUPPORT_SYSTEM_PROMPT}\n\n"
            f"## Current Session\n"
            f"Current customer user_id: {user_id}\n"
            f"{profile_block}\n"
            f"If authenticated name is present, use it for personalization when appropriate.\n"
            "Account-related tools are already scoped to this current customer.\n"
            "Never ask for or operate on a different user_id."
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
                    safe_args = _filter_tool_args(tool_fn, tool_call.get("args"))
                    result = await tool_fn.ainvoke(safe_args)
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
