"""Evolution API webhook routes.

Handles incoming WhatsApp events from Evolution API.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Request
from langchain_core.messages import AIMessage, HumanMessage

import src.container as container
from src.agents.swarm_config import build_swarm_config
from src.api.security import enforce_sensitive_endpoint_auth
from src.infrastructure.whatsapp import client as whatsapp_client
from src.infrastructure.whatsapp.session_store import session_store
from src.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Webhook"])


def _extract_message_text(data: dict[str, Any]) -> str:
    """Extract text from common Evolution message payload shapes."""
    msg = data.get("message", {})
    return (
        msg.get("conversation")
        or msg.get("extendedTextMessage", {}).get("text")
        or msg.get("imageMessage", {}).get("caption")
        or ""
    ).strip()


def _is_operator_system_message(text: str) -> bool:
    """Identify escalation/system templates sent by the backend itself."""
    if not text:
        return True
    upper_text = text.upper()
    if text.startswith("🚨 *ESCALAMENTO"):
        return True
    if "ESCALAMENTO" in upper_text:
        return True
    if "SESS" in upper_text and "ESC-" in upper_text:
        return True
    if text.startswith("*[User "):
        return True
    # Chat->operator bridge format: *<name>:* <message>
    if re.match(r"^\*[^*:\n]{1,120}:\*\s", text):
        return True
    return False


async def process_whatsapp_message(phone: str, text: str, message_id: str) -> None:
    """Run the swarm in background and reply to WhatsApp."""
    session = session_store.get_session_by_user(phone)
    if session and session.active:
        # User is in human handoff: forward to operator and skip AI.
        session_store.add_message(session.session_id, sender="user", content=text)
        if settings.whatsapp_enabled:
            whatsapp_client.send_message(session.operator_number, f"*[User {phone}]:* {text}")
        return

    swarm = await container.get_swarm()
    config = build_swarm_config(
        thread_id=phone,
        checkpoint_ns="whatsapp",
        fallback_thread_id="whatsapp_user",
    )
    configurable = config["configurable"]
    thread_id = configurable["thread_id"]
    checkpoint_ns = configurable["checkpoint_ns"]

    initial_state = {
        "messages": [HumanMessage(content=text)],
        "user_id": thread_id,
        "intent": "",
        "language": "pt-BR",
        "agent_route": "",
        "sentiment_score": 0.0,
        "escalated": False,
        "guardrail_blocked": False,
        "guardrail_reason": "",
        "metadata": {},
    }

    try:
        logger.info(
            "[Webhook] Invoking swarm user=%s thread_id=%s checkpoint_ns=%s message_id=%s",
            phone,
            thread_id,
            checkpoint_ns,
            message_id,
        )
        result = await swarm.ainvoke(initial_state, config=config)

        response_text = ""
        for msg in reversed(result.get("messages", [])):
            if not isinstance(msg, AIMessage):
                continue
            content = (getattr(msg, "content", "") or "").strip()
            if not content:
                continue
            name = (getattr(msg, "name", "") or "").strip()
            if name == "router":
                continue
            response_text = content
            break

        if not response_text:
            response_text = "Desculpe, ocorreu um erro ao processar sua solicitacao."

        wa_text = response_text.replace("**", "*")
        if settings.whatsapp_enabled:
            whatsapp_client.send_message(phone, wa_text)
        else:
            logger.info("[Webhook] Simulated reply to %s: %s", phone, wa_text)

    except Exception as exc:
        logger.error(
            "[Webhook] Error processing swarm user=%s thread_id=%s checkpoint_ns=%s message_id=%s: %s",
            phone,
            thread_id,
            checkpoint_ns,
            message_id,
            exc,
            exc_info=True,
        )
        if settings.whatsapp_enabled:
            whatsapp_client.send_message(
                phone,
                "Desculpe, nossos sistemas estao instaveis no momento. Tente novamente mais tarde.",
            )


@router.post(
    "/webhook",
    summary="Evolution API webhook",
    description="Receives MESSAGES_UPSERT events and processes them in background.",
)
async def evolution_webhook(request: Request, background_tasks: BackgroundTasks) -> dict:
    """Handle incoming requests from Evolution API."""
    enforce_sensitive_endpoint_auth(request)
    payload = await request.json()

    event = str(payload.get("event") or "")
    normalized_event = event.lower().replace("_", ".")
    if normalized_event != "messages.upsert":
        return {"status": "ignored", "reason": f"event {event}"}

    data = payload.get("data", {})
    key = data.get("key", {})
    remote_jid = key.get("remoteJid", "")
    if "@g.us" in remote_jid:
        return {"status": "ignored", "reason": "group_message"}

    phone = remote_jid.replace("@s.whatsapp.net", "").replace("@c.us", "")
    text = _extract_message_text(data)
    if not text:
        return {"status": "ignored", "reason": "no_text"}

    from_me = bool(key.get("fromMe"))
    message_id = key.get("id", "")
    logger.info(
        "[Webhook] event=messages.upsert from_me=%s phone=%s message_id=%s text=%s",
        from_me,
        phone,
        message_id,
        text[:120],
    )

    # Operator reply path: when a human handoff session exists for this number,
    # store message for UI polling.
    session = session_store.get_session_by_operator_number(phone)
    if session and session.active:
        session_store.bind_operator_number(session.session_id, phone)
        if not from_me:
            session_store.add_message(session.session_id, sender="agent", content=text)
            logger.info(
                "[Webhook] stored operator reply session=%s phone=%s",
                session.session_id,
                phone,
            )
            return {"status": "ok", "role": "operator", "session_id": session.session_id}

        # Compatibility for self-chat operation (operator == bot account).
        if not _is_operator_system_message(text):
            session_store.add_message(session.session_id, sender="agent", content=text)
            logger.info(
                "[Webhook] stored self-chat operator reply session=%s phone=%s",
                session.session_id,
                phone,
            )
            return {"status": "ok", "role": "operator_self", "session_id": session.session_id}

        return {"status": "ignored", "reason": "operator_system_forward"}

    if from_me:
        # Last-resort fallback for self-chat when configured operator number
        # does not exactly match remoteJid.
        if not _is_operator_system_message(text):
            active_sessions = session_store.get_active_sessions()
            if active_sessions:
                # Prefer the latest active session to keep handoff continuity.
                fallback_session = max(active_sessions, key=lambda session: session.created_at)
                session_store.bind_operator_number(fallback_session.session_id, phone)
                session_store.add_message(fallback_session.session_id, sender="agent", content=text)
                logger.info(
                    "[Webhook] fallback stored self-chat reply session=%s phone=%s",
                    fallback_session.session_id,
                    phone,
                )
                return {
                    "status": "ok",
                    "role": "operator_self_fallback",
                    "session_id": fallback_session.session_id,
                }
        return {"status": "ignored", "reason": "from_me"}

    background_tasks.add_task(process_whatsapp_message, phone, text, message_id)
    return {"status": "ok", "task": "queued"}
