"""Sentiment & Escalation Agent node.

Analyzes conversation sentiment and triggers human escalation when needed.
This is the 4th bonus agent that handles the "redirect to human" requirement.
"""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage

from src.agents.prompts.sentiment_prompt import SENTIMENT_SYSTEM_PROMPT
from src.agents.state import AgentState
from src.agents.tools.sentiment_tools import (
    analyze_sentiment,
    detect_urgency,
    escalate_to_human,
    generate_escalation_summary,
)
from src.infrastructure.llm.model_factory import get_sentiment_llm

logger = logging.getLogger(__name__)

_SENTIMENT_TOOLS = [
    analyze_sentiment,
    detect_urgency,
    escalate_to_human,
    generate_escalation_summary,
]


async def sentiment_node(state: AgentState) -> dict:
    """Analyze sentiment and decide on escalation.

    Flow:
    1. Analyze the sentiment of the conversation
    2. Detect urgency level
    3. If critical/high → trigger escalation and notify user
    4. If low/medium → provide assessment without escalating
    """
    llm = get_sentiment_llm().bind_tools(_SENTIMENT_TOOLS)
    user_id = state.get("user_id", "unknown")

    context_prompt = (
        f"{SENTIMENT_SYSTEM_PROMPT}\n\n"
        f"## Current Session\n"
        f"Customer user_id: {user_id}"
    )

    messages = [SystemMessage(content=context_prompt)] + list(state["messages"])

    # Tool-calling loop (max 3 rounds)
    for _ in range(3):
        response = await llm.ainvoke(messages)

        if not response.tool_calls:
            break

        tool_map = {t.name: t for t in _SENTIMENT_TOOLS}
        tool_messages = []

        for tool_call in response.tool_calls:
            tool_fn = tool_map.get(tool_call["name"])
            if tool_fn:
                logger.info("Sentiment agent calling tool: %s", tool_call["name"])
                result = tool_fn.invoke(tool_call["args"])
                tool_messages.append(
                    ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call["id"],
                    )
                )

        messages = messages + [response] + tool_messages

    # Determine if escalation happened
    escalated = "ESCALATION TRIGGERED" in response.content

    return {
        "messages": [
            AIMessage(content=response.content, name="sentiment")
        ],
        "escalated": escalated,
        "sentiment_score": state.get("sentiment_score", 0.0),
    }
