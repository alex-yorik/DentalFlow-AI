import hashlib
import logging
import os
from typing import Any, cast

from fastapi import APIRouter, Request
from pydantic import BaseModel

from src.channels.base import IncomingMessage
from src.core.lead_lookup import resolve_lead
from src.core.message_processor import process_message
from src.leads.models import Lead

logger = logging.getLogger(__name__)

router = APIRouter()

# WhatsApp Business API integration (not yet configured)
# Requires: WhatsApp Business Account + Meta Developer setup
# See: https://developers.facebook.com/docs/whatsapp/business-api/
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")


class WhatsAppOutgoingAdapter:
    def __init__(self, phone_number: str) -> None:
        self._phone = phone_number
        self.sent: list[str] = []

    async def send_message(self, channel_user_id: str, text: str) -> None:
        phone = channel_user_id or self._phone
        self.sent.append(text)
        logger.info("WhatsApp stub: would send to %s: %s", phone, text[:80])


class WhatsAppMessage(BaseModel):
    phone_number: str
    text: str


class WhatsAppWebhookPayload(BaseModel):
    object: str = "whatsapp_business_account"
    entry: list[dict[str, Any]] = []


def _phone_to_int(phone: str) -> int:
    return int(hashlib.sha256(phone.encode("utf-8")).hexdigest(), 16) & 0x7FFFFFFF


@router.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request, body: WhatsAppMessage) -> dict:
    config = request.app.state.config
    llm_client = request.app.state.llm_client

    chat_id = _phone_to_int(body.phone_number)

    lead, blocked_reply = await resolve_lead(
        chat_id,
        source="whatsapp",
        channel_type="whatsapp",
        blocked_reply=config.client.business.messages.get("error_unsafe", ""),
    )
    if blocked_reply:
        return {"reply": blocked_reply}

    lead = cast(Lead, lead)

    msg = IncomingMessage(
        channel_user_id=body.phone_number,
        text=body.text,
        channel_type="whatsapp",
    )
    outgoing = WhatsAppOutgoingAdapter(body.phone_number)

    await process_message(
        msg=msg,
        outgoing=outgoing,
        lead=lead,
        config=config,
        llm_client=llm_client,
    )

    reply = outgoing.sent[-1] if outgoing.sent else ""
    return {"reply": reply}


@router.get("/whatsapp/webhook")
async def whatsapp_verify(hub_mode: str = "", hub_verify_token: str = "", hub_challenge: str = "") -> dict | str:
    if VERIFY_TOKEN and hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified")
        return hub_challenge
    logger.warning("WhatsApp webhook verification failed: mode=%s", hub_mode)
    return {"error": "verification failed"}