"""Chat route — The main API endpoint.

POST /v1/chat accepts {message, user_id} and processes through the agent swarm.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage

from src.api.v1.schemas import ChatRequest, ChatResponse, ErrorResponse
from src.infrastructure.llm.model_factory import get_router_llm  # noqa: F401

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Process a chat message through the agent swarm",
    description=(
        "Send a message to the InfinitePay AI agent swarm. "
        "The router agent classifies the intent and delegates to "
        "the appropriate specialized agent."
    ),
)
async def chat(request: ChatRequest) -> ChatResponse:
    """Main chat endpoint — the entry point for all user messages.

    Flow:
    1. Validate the request
    2. Create the initial agent state
    3. Invoke the LangGraph swarm
    4. Extract and return the agent response
    """
    from src.main import get_swarm

    swarm = get_swarm()

    try:
        # Build initial state
        initial_state = {
            "messages": [HumanMessage(content=request.message)],
            "user_id": request.user_id,
            "intent": "",
            "language": "pt-BR",
            "agent_route": "",
            "sentiment_score": 0.0,
            "escalated": False,
            "guardrail_blocked": False,
            "guardrail_reason": "",
            "metadata": {},
        }

        # Invoke the swarm
        logger.info("Processing message for user=%s: %s", request.user_id, request.message[:100])
        result = await swarm.ainvoke(initial_state)

        # Extract the final response (last AI message)
        response_text = ""
        agent_used = "router"

        for msg in reversed(result.get("messages", [])):
            if hasattr(msg, "content") and msg.content:
                name = getattr(msg, "name", "")
                # Skip internal router messages
                if name != "router" and name != "guardrail":
                    response_text = msg.content
                    agent_used = name or "unknown"
                    break
                elif name == "guardrail":
                    response_text = msg.content
                    agent_used = "guardrail"
                    break

        if not response_text:
            response_text = "I'm sorry, I couldn't process your request. Please try again."

        return ChatResponse(
            response=response_text,
            agent_used=agent_used,
            intent=result.get("intent", ""),
            language=result.get("language", "pt-BR"),
            metadata={
                "escalated": result.get("escalated", False),
                "guardrail_blocked": result.get("guardrail_blocked", False),
                **result.get("metadata", {}),
            },
        )

    except Exception as e:
        logger.error("Error processing chat message: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal error processing message: {str(e)}",
        )
