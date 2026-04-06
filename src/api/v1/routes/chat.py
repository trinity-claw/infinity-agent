"""Chat routes (standard + streaming)."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage

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


def _is_ai_message(message: Any) -> bool:
    """Return True only for AIMessage instances."""
    return isinstance(message, AIMessage)


def _extract_final_agent_response(result: dict[str, Any]) -> tuple[str, str]:
    """Extract final assistant response text and agent name from swarm result.

    Important:
    - Never return human/user messages as assistant output.
    - Skip router trace messages.
    """
    for message in reversed(result.get("messages", [])):
        if not _is_ai_message(message):
            continue

        content = (getattr(message, "content", "") or "").strip()
        if not content:
            continue

        name = (getattr(message, "name", "") or "").strip()
        if name == "router":
            continue

        return content, (name or "unknown")

    return "I'm sorry, I couldn't process your request. Please try again.", "unknown"


def _sse_event(event: str, payload: dict[str, Any]) -> str:
    """Format one SSE event block."""
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _chunk_text(text: str, chunk_size: int = 22) -> list[str]:
    """Split text into UI-friendly streaming chunks."""
    if not text:
        return []
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


async def _resolve_handoff_contact(
    thread_id: str,
    authenticated_user: dict[str, str],
) -> dict[str, str]:
    """Resolve best-effort contact data for human handoff notice."""
    contact = {
        "name": authenticated_user.get("name", "") if authenticated_user else "",
        "email": authenticated_user.get("email", "") if authenticated_user else "",
        "phone": "",
    }

    try:
        user_repo = container.get_user_repository()
        user = await user_repo.find_by_id(thread_id)
        if user is None and contact["email"]:
            user = await user_repo.find_by_email(contact["email"])
        if user:
            if not contact["name"]:
                contact["name"] = user.name
            if not contact["email"]:
                contact["email"] = user.email
            contact["phone"] = user.phone
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.warning("Unable to resolve handoff contact details: %s", exc)

    if not contact["name"]:
        contact["name"] = thread_id
    if not contact["email"]:
        contact["email"] = "nao_informado"
    if not contact["phone"]:
        contact["phone"] = "nao_informado"
    return contact


def _handoff_notice_text(session_id: str, reason: str, contact: dict[str, str]) -> str:
    """Build enriched human handoff notice for operator WhatsApp."""
    return (
        "📌 *DETALHES DO ATENDIMENTO HUMANO*\n\n"
        f"*Sessão:* {session_id}\n"
        f"*Motivo:* {reason or 'Escalonamento solicitado'}\n"
        f"*Cliente:* {contact.get('name')}\n"
        f"*Email do cliente:* {contact.get('email')}\n"
        f"*Telefone do cliente:* {contact.get('phone')}\n\n"
        "Canal de continuidade: atendimento assíncrono por WhatsApp e/ou e-mail."
    )


def _append_async_handoff_note(text: str) -> str:
    """Append explicit asynchronous handoff channel note."""
    note = (
        "\n\nA continuidade do atendimento humano ocorrerá por WhatsApp e/ou e-mail "
        "cadastrado (fluxo assíncrono)."
    )
    if note.strip() in (text or ""):
        return text
    return f"{text}{note}"


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

        response_text, agent_used = _extract_final_agent_response(result)

        extra_metadata: dict = {}
        if result.get("escalated", False):
            active_session = session_store.get_session_by_user(thread_id)
            if active_session:
                extra_metadata["session_id"] = active_session.session_id
                if settings.whatsapp_enabled and not session_store.is_detail_notice_sent(active_session.session_id):
                    contact = await _resolve_handoff_contact(thread_id, authenticated_user)
                    reason = str(result.get("metadata", {}).get("escalation_reason", "")).strip()
                    whatsapp_client.send_message(
                        active_session.operator_number,
                        _handoff_notice_text(active_session.session_id, reason, contact),
                    )
                    session_store.mark_detail_notice_sent(active_session.session_id)
            response_text = _append_async_handoff_note(response_text)
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


async def _chat_stream_generator(request: ChatRequest) -> AsyncGenerator[str, None]:
    """Stream chat processing as SSE status + token events."""
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

    yield _sse_event("status", {"message": "Recebido. Iniciando fluxo do agente..."})

    if request.session_id:
        session = session_store.get_session(request.session_id)
        if session and session.active:
            session_store.add_message(request.session_id, sender="user", content=request.message)
            if settings.whatsapp_enabled:
                whatsapp_client.send_message(
                    session.operator_number,
                    f"*{sender_label}:* {request.message}",
                )

            final_payload = {
                "response": "Mensagem enviada ao atendente. Aguarde a resposta.",
                "agent_used": "human",
                "intent": "escalation",
                "language": "pt-BR",
                "metadata": {
                    "escalated": True,
                    "guardrail_blocked": False,
                    "session_id": request.session_id,
                    **(
                        {"authenticated_user": authenticated_user}
                        if authenticated_user
                        else {}
                    ),
                },
            }
            for chunk in _chunk_text(final_payload["response"]):
                yield _sse_event("token", {"delta": chunk})
                await asyncio.sleep(0)
            yield _sse_event("final", final_payload)
            yield _sse_event("done", {"ok": True})
            return

    try:
        swarm = await container.get_swarm()

        initial_metadata: dict[str, Any] = {}
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
            "Streaming swarm user=%s thread_id=%s checkpoint_ns=%s",
            request.user_id,
            thread_id,
            checkpoint_ns,
        )

        final_text = ""
        agent_used = "unknown"
        intent = ""
        language = "pt-BR"
        escalated = False
        guardrail_blocked = False
        merged_metadata: dict[str, Any] = {}

        async for update in swarm.astream(
            initial_state,
            config=swarm_config,
            stream_mode="updates",
        ):
            if not isinstance(update, dict):
                continue

            for node_name, node_update in update.items():
                if node_name == "input_guard":
                    yield _sse_event("status", {"message": "Validando segurança da mensagem..."})
                elif node_name == "router":
                    yield _sse_event("status", {"message": "Router classificando intenção..."})
                elif node_name == "knowledge":
                    yield _sse_event("status", {"message": "Consultando base e web..."})
                elif node_name == "support":
                    yield _sse_event("status", {"message": "Executando ferramentas de suporte..."})
                elif node_name == "sentiment":
                    yield _sse_event("status", {"message": "Avaliando urgência/escalonamento..."})
                elif node_name == "output_guard":
                    yield _sse_event("status", {"message": "Finalizando resposta..."})

                if not isinstance(node_update, dict):
                    continue

                if node_name == "router":
                    intent = node_update.get("intent", intent)
                    language = node_update.get("language", language)

                escalated = bool(node_update.get("escalated", escalated))
                guardrail_blocked = bool(node_update.get("guardrail_blocked", guardrail_blocked))
                merged_metadata.update(node_update.get("metadata", {}))

                for message in node_update.get("messages", []) or []:
                    if not _is_ai_message(message):
                        continue
                    content = (getattr(message, "content", "") or "").strip()
                    if not content:
                        continue
                    name = (getattr(message, "name", "") or node_name).strip()
                    if name == "router":
                        continue
                    final_text = content
                    agent_used = name or "unknown"
                    if agent_used == "guardrail":
                        guardrail_blocked = True

        if not final_text:
            final_text = "Desculpe, não consegui processar sua mensagem. Tente novamente."

        if escalated:
            active_session = session_store.get_session_by_user(thread_id)
            if active_session:
                merged_metadata["session_id"] = active_session.session_id
                if settings.whatsapp_enabled and not session_store.is_detail_notice_sent(active_session.session_id):
                    contact = await _resolve_handoff_contact(thread_id, authenticated_user)
                    reason = str(merged_metadata.get("escalation_reason", "")).strip()
                    whatsapp_client.send_message(
                        active_session.operator_number,
                        _handoff_notice_text(active_session.session_id, reason, contact),
                    )
                    session_store.mark_detail_notice_sent(active_session.session_id)
            final_text = _append_async_handoff_note(final_text)
        if authenticated_user:
            merged_metadata["authenticated_user"] = authenticated_user

        final_payload = {
            "response": final_text,
            "agent_used": agent_used,
            "intent": intent,
            "language": language,
            "metadata": {
                "escalated": escalated,
                "guardrail_blocked": guardrail_blocked,
                **merged_metadata,
            },
        }

        for chunk in _chunk_text(final_text):
            yield _sse_event("token", {"delta": chunk})
            await asyncio.sleep(0)

        yield _sse_event("final", final_payload)
        yield _sse_event("done", {"ok": True})
    except Exception as exc:
        logger.error(
            "Error streaming chat message user=%s thread_id=%s checkpoint_ns=%s: %s",
            request.user_id,
            thread_id,
            checkpoint_ns,
            str(exc),
            exc_info=True,
        )
        yield _sse_event(
            "error",
            {"detail": f"Internal error processing message: {str(exc)}"},
        )
        yield _sse_event("done", {"ok": False})


@router.post(
    "/chat/stream",
    summary="Stream a chat response through the agent swarm",
    description=(
        "Streams status and response chunks (SSE) while the swarm is processing. "
        "Useful for frontend progress indicators."
    ),
)
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    """Streaming chat endpoint (SSE)."""
    return StreamingResponse(
        _chat_stream_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
