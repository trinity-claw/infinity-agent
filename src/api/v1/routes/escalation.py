"""Escalation routes - WhatsApp webhook + message polling.

Two endpoints:

  POST /v1/webhook/whatsapp
      Receives incoming messages from the operator's WhatsApp.

  GET /v1/messages/{session_id}?since=N
      Frontend polls this every few seconds to receive new operator messages.

  POST /v1/messages/{session_id}
      Frontend posts a user message directly to an escalated session
      (bypasses the swarm - goes straight to operator via WhatsApp).
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from src.api.security import enforce_sensitive_endpoint_auth
from src.infrastructure.whatsapp import client as whatsapp_client
from src.infrastructure.whatsapp.session_store import session_store
from src.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Escalation"])


def _resolve_session_token(request: Request, provided_token: str | None) -> str:
    """Resolve session token from query/body or header."""
    return (
        (provided_token or "").strip()
        or (request.headers.get("x-session-token") or "").strip()
    )


@router.post(
    "/webhook/whatsapp",
    summary="WhatsApp webhook - receives operator replies",
)
async def whatsapp_webhook(request: Request, payload: dict[str, Any]) -> dict:
    """Handle incoming WhatsApp messages from the human operator."""
    enforce_sensitive_endpoint_auth(request)

    try:
        data = payload.get("data", {})
        key = data.get("key", {})

        if key.get("fromMe"):
            return {"status": "ignored"}

        raw_jid: str = key.get("remoteJid", "")
        phone = raw_jid.replace("@s.whatsapp.net", "").replace("@c.us", "")

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
            "[Webhook] operator message stored in session %s: %s...",
            session.session_id,
            text[:60],
        )
        return {"status": "ok", "session_id": session.session_id}

    except Exception as exc:
        logger.error("[Webhook] error processing payload: %s", exc, exc_info=True)
        return {"status": "error"}


@router.get(
    "/messages/{session_id}",
    summary="Poll for new operator messages in an escalated session",
)
async def poll_messages(
    request: Request,
    session_id: str,
    since: int = 0,
    session_token: str | None = Query(None),
) -> dict:
    """Return messages in the escalated session starting from index `since`."""
    enforce_sensitive_endpoint_auth(request)

    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    resolved_token = _resolve_session_token(request, session_token)
    if not session_store.validate_session_token(session_id, resolved_token):
        raise HTTPException(status_code=403, detail="Invalid escalation session credentials")

    messages = session_store.get_messages(session_id, since=since)
    return {
        "session_id": session_id,
        "active": session.active,
        "messages": messages,
        "total": len(session.messages),
    }


class UserMessageRequest(BaseModel):
    content: str
    user_id: str
    session_token: str | None = None


@router.post(
    "/messages/{session_id}",
    summary="Forward a user message to the operator via WhatsApp",
)
async def send_user_message(request: Request, session_id: str, body: UserMessageRequest) -> dict:
    """Store the user message and forward it to the operator via WhatsApp."""
    enforce_sensitive_endpoint_auth(request)

    session = session_store.get_session(session_id)
    if not session or not session.active:
        raise HTTPException(status_code=404, detail="Session not found or closed")

    resolved_token = _resolve_session_token(request, body.session_token)
    if not session_store.validate_session_token(session_id, resolved_token):
        raise HTTPException(status_code=403, detail="Invalid escalation session credentials")

    session_store.add_message(session_id, sender="user", content=body.content)

    if settings.whatsapp_enabled:
        user_text = f"*{body.user_id}:* {body.content}"
        whatsapp_client.send_message(session.operator_number, user_text)

    return {"status": "sent", "session_id": session_id}
