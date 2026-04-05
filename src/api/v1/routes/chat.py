"""Chat route."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage

import src.container as container
from src.agents.swarm_config import build_swarm_config, sanitize_identifier
from src.api.v1.schemas import ChatRequest, ChatResponse, ErrorResponse
from src.infrastructure.whatsapp import client as whatsapp_client
from src.infrastructure.whatsapp.session_store import session_store
from src.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])


def _build_authenticated_user(request: ChatRequest) -> dict[str, str]:
    """Extract authenticated profile fields from the request."""
    profile: dict[str, str] = {}
    if request.user_name:
        clean_name = request.user_name.strip()
        if clean_name:
            profile["name"] = clean_name
    if request.user_email:
        clean_email = request.user_email.strip().lower()
        if clean_email:
            profile["email"] = clean_email
    return profile


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
    """Main chat endpoint."""
    authenticated_user = _build_authenticated_user(request)
    fallback_user = sanitize_identifier(authenticated_user.get("email"), fallback="client_web")
    thread_id = sanitize_identifier(request.user_id, fallback=fallback_user)
    swarm_config = build_swarm_config(
        thread_id=thread_id,
        checkpoint_ns="chat",
        fallback_thread_id=fallback_user,
    )
    configurable = swarm_config["configurable"]
    thread_id = configurable["thread_id"]
    checkpoint_ns = configurable["checkpoint_ns"]
    sender_label = authenticated_user.get("name", thread_id)

    if request.session_id:
        session = session_store.get_session(request.session_id)
        if session and session.active:
            session_store.add_message(request.session_id, sender="user", content=request.message)
            if settings.whatsapp_enabled:
                whatsapp_client.send_message(
                    session.operator_number,
                    f"*{sender_label}:* {request.message}",
                )

            metadata = {
                "escalated": True,
                "guardrail_blocked": False,
                "session_id": request.session_id,
            }
            if authenticated_user:
                metadata["authenticated_user"] = authenticated_user

            return ChatResponse(
                response="Mensagem enviada ao atendente. Aguarde a resposta.",
                agent_used="human",
                intent="escalation",
                language="pt-BR",
                metadata=metadata,
            )

    try:
        swarm = await container.get_swarm()

        initial_metadata: dict = {}
        if authenticated_user:
            initial_metadata["authenticated_user"] = authenticated_user

        initial_state = {
            "messages": [HumanMessage(content=request.message)],
            "user_id": thread_id,
            "intent": "",
            "language": "pt-BR",
            "agent_route": "",
            "sentiment_score": 0.0,
            "escalated": False,
            "guardrail_blocked": False,
            "guardrail_reason": "",
            "metadata": initial_metadata,
        }

        logger.info(
            "Invoking swarm user=%s thread_id=%s checkpoint_ns=%s",
            request.user_id,
            thread_id,
            checkpoint_ns,
        )

        result = await swarm.ainvoke(
            initial_state,
            config=swarm_config,
        )

        response_text = ""
        agent_used = "router"
        for message in reversed(result.get("messages", [])):
            if hasattr(message, "content") and message.content:
                name = getattr(message, "name", "")
                if name not in {"router", "guardrail"}:
                    response_text = message.content
                    agent_used = name or "unknown"
                    break
                if name == "guardrail":
                    response_text = message.content
                    agent_used = "guardrail"
                    break

        if not response_text:
            response_text = "I'm sorry, I couldn't process your request. Please try again."

        extra_metadata: dict = {}
        if result.get("escalated", False):
            active_session = session_store.get_session_by_user(thread_id)
            if active_session:
                extra_metadata["session_id"] = active_session.session_id
        if authenticated_user:
            extra_metadata["authenticated_user"] = authenticated_user

        return ChatResponse(
            response=response_text,
            agent_used=agent_used,
            intent=result.get("intent", ""),
            language=result.get("language", "pt-BR"),
            metadata={
                "escalated": result.get("escalated", False),
                "guardrail_blocked": result.get("guardrail_blocked", False),
                **result.get("metadata", {}),
                **extra_metadata,
            },
        )
    except Exception as exc:
        logger.error(
            "Error processing chat message user=%s thread_id=%s checkpoint_ns=%s: %s",
            request.user_id,
            thread_id,
            checkpoint_ns,
            str(exc),
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal error processing message: {str(exc)}",
        ) from exc
