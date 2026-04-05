"""Escalation routes — WhatsApp webhook + message polling.

Two endpoints:

  POST /v1/webhook/whatsapp
      Receives incoming messages from the operator's WhatsApp.
      Evolution API sends a JSON payload; we extract the sender's
      phone number and message text, find the active session, and
      store the message so the frontend can poll for it.

  GET /v1/messages/{session_id}?since=N
      Frontend polls this every few seconds to receive new operator
      messages. Returns only messages after index N.

  POST /v1/messages/{session_id}
      Frontend posts a user message directly to an escalated session
      (bypasses the swarm — goes straight to operator via WhatsApp).
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.infrastructure.whatsapp import client as whatsapp_client
from src.infrastructure.whatsapp.session_store import session_store
from src.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Escalation"])


# ── Webhook (Evolution API format) ────────────────────────────────────────────

@router.post(
    "/webhook/whatsapp",
    summary="WhatsApp webhook — receives operator replies",
)
async def whatsapp_webhook(payload: dict[str, Any]) -> dict:
    """Handle incoming WhatsApp messages from the human operator.

    Expected payload shape (Evolution API MESSAGES_UPSERT):
    {
      "event": "MESSAGES_UPSERT",
      "data": {
        "key": {"remoteJid": "5511999999999@s.whatsapp.net", "fromMe": false},
        "message": {"conversation": "texto da mensagem"}
      }
    }
    """
    try:
        data = payload.get("data", {})
        key = data.get("key", {})

        # Skip messages sent by the bot itself
        if key.get("fromMe"):
            return {"status": "ignored"}

        raw_jid: str = key.get("remoteJid", "")
        phone = raw_jid.replace("@s.whatsapp.net", "").replace("@c.us", "")

        # Extract message text from various Evolution API formats
        msg = data.get("message", {})
        text = (
            msg.get("conversation")
            or msg.get("extendedTextMessage", {}).get("text")
            or msg.get("imageMessage", {}).get("caption")
            or ""
        ).strip()

        if not text:
            return {"status": "no_text"}

        session = session_store.get_session_by_operator_number(phone)
        if not session:
            logger.warning("[Webhook] no active session for operator number %s", phone)
            return {"status": "no_session"}

        session_store.add_message(session.session_id, sender="agent", content=text)
        logger.info(
            "[Webhook] operator message stored in session %s: %s…",
            session.session_id, text[:60],
        )
        return {"status": "ok", "session_id": session.session_id}

    except Exception as exc:
        logger.error("[Webhook] error processing payload: %s", exc, exc_info=True)
        # Return 200 so Evolution API doesn't retry indefinitely
        return {"status": "error", "detail": str(exc)}


# ── Message polling ────────────────────────────────────────────────────────────

@router.get(
    "/messages/{session_id}",
    summary="Poll for new operator messages in an escalated session",
)
async def poll_messages(session_id: str, since: int = 0) -> dict:
    """Return messages in the escalated session starting from index `since`."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = session_store.get_messages(session_id, since=since)
    return {
        "session_id": session_id,
        "active": session.active,
        "messages": messages,
        "total": len(session.messages),
    }


# ── User sends message to operator ────────────────────────────────────────────

class UserMessageRequest(BaseModel):
    content: str
    user_id: str


@router.post(
    "/messages/{session_id}",
    summary="Forward a user message to the operator via WhatsApp",
)
async def send_user_message(session_id: str, body: UserMessageRequest) -> dict:
    """Store the user message and forward it to the operator via WhatsApp."""
    session = session_store.get_session(session_id)
    if not session or not session.active:
        raise HTTPException(status_code=404, detail="Session not found or closed")

    session_store.add_message(session_id, sender="user", content=body.content)

    if settings.whatsapp_enabled:
        user_text = f"*{body.user_id}:* {body.content}"
        whatsapp_client.send_message(session.operator_number, user_text)

    return {"status": "sent", "session_id": session_id}
