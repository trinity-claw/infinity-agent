"""WhatsApp HTTP client — compatible with Evolution API and Z-API.

Sends messages via a REST API. Configure via environment variables:

  WHATSAPP_ENABLED=true
  WHATSAPP_API_URL=https://your-evolution-api-host
  WHATSAPP_API_TOKEN=your_api_key
  WHATSAPP_INSTANCE=main              # Evolution API instance name
  WHATSAPP_OPERATOR_NUMBER=5511999999999

When WHATSAPP_ENABLED=false (default) the client is a no-op — useful for
development and test environments that don't have a WhatsApp connection.
"""

from __future__ import annotations

import logging

import httpx

from src.settings import settings

logger = logging.getLogger(__name__)


def send_message(to_number: str, text: str) -> bool:
    """Send a text message via WhatsApp.

    Compatible with:
    - Evolution API: POST /message/sendText/{instance}
    - Z-API:         POST /send-text  (adapt URL in settings)

    Returns True on success, False on failure or when disabled.
    """
    if not settings.whatsapp_enabled:
        logger.info("[WhatsApp] disabled — message to %s not sent", to_number)
        return False

    if not settings.whatsapp_api_url or not settings.whatsapp_operator_number:
        logger.warning("[WhatsApp] WHATSAPP_API_URL or WHATSAPP_OPERATOR_NUMBER not set")
        return False

    url = (
        f"{settings.whatsapp_api_url.rstrip('/')}"
        f"/message/sendText/{settings.whatsapp_instance}"
    )
    payload = {"number": to_number, "text": text}
    headers = {
        "Content-Type": "application/json",
        "apikey": settings.whatsapp_api_token,
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            logger.info("[WhatsApp] message sent to %s (%d)", to_number, resp.status_code)
            return True
    except httpx.HTTPStatusError as exc:
        logger.error("[WhatsApp] HTTP error %s: %s", exc.response.status_code, exc.response.text)
    except httpx.RequestError as exc:
        logger.error("[WhatsApp] request error: %s", exc)

    return False
