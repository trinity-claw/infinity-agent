"""Evolution API Webhook Routes.

Handles incoming messages from WhatsApp users via Evolution API.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Request
from langchain_core.messages import HumanMessage

import src.container as container
from src.agents.swarm_config import build_swarm_config
from src.infrastructure.whatsapp import client as whatsapp_client
from src.infrastructure.whatsapp.session_store import session_store
from src.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Webhook"])


async def process_whatsapp_message(phone: str, text: str, message_id: str) -> None:
    """Run the agent swarm in the background and reply to WhatsApp."""
    # Check if this user is currently in a human handoff session
    session = session_store.get_session_by_user(phone)
    if session and session.active:
        # User is talking to a human operator — forward message and skip AI
        session_store.add_message(session.session_id, sender="user", content=text)
        if settings.whatsapp_enabled:
            # We prefix so the operator knows who is talking
            whatsapp_client.send_message(
                session.operator_number,
                f"*[User {phone}]:* {text}"
            )
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

    # Initial state
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

        # Extract final AI response
        response_text = ""
        for msg in reversed(result.get("messages", [])):
            if hasattr(msg, "content") and msg.content:
                name = getattr(msg, "name", "")
                if name not in ("router"):
                    response_text = msg.content
                    break

        if not response_text:
            response_text = "Desculpe, ocorreu um erro ao processar sua solicitação."

        # Map Markdown bold to WhatsApp bold
        wa_text = response_text.replace("**", "*")

        # Reply via WhatsApp
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
                "Desculpe, nossos sistemas estão instáveis no momento. Tente novamente mais tarde."
            )


@router.post(
    "/webhook",
    summary="Evolution API Webhook",
    description="Receives MESSAGES_UPSERT events and processes them in background.",
)
async def evolution_webhook(request: Request, background_tasks: BackgroundTasks) -> dict:
    """Handle incoming requests from Evolution API."""
    payload = await request.json()
    
    # We only care about MESSAGES_UPSERT events
    event = payload.get("event")
    if event != "messages.upsert":
        # Evolution API sends connection updates too
        return {"status": "ignored", "reason": f"event {event}"}

    data = payload.get("data", {})
    key = data.get("key", {})

    # Ignore our own messages
    if key.get("fromMe"):
        return {"status": "ignored", "reason": "from_me"}

    # Ignore group messages
    remote_jid = key.get("remoteJid", "")
    if "@g.us" in remote_jid:
        return {"status": "ignored", "reason": "group_message"}

    # Clean phone number
    phone = remote_jid.replace("@s.whatsapp.net", "").replace("@c.us", "")

    # Extract text from various Evolution API message formats
    msg = data.get("message", {})
    text = (
        msg.get("conversation")
        or msg.get("extendedTextMessage", {}).get("text")
        or msg.get("imageMessage", {}).get("caption")
        or ""
    ).strip()

    if not text:
        return {"status": "ignored", "reason": "no_text"}

    message_id = key.get("id", "")

    # Dispatch to background task to free the HTTP request immediately
    background_tasks.add_task(process_whatsapp_message, phone, text, message_id)

    return {"status": "ok", "task": "queued"}
