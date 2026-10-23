import hashlib
import logging
import os
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from src.channels.base import IncomingMessage, OutgoingAdapter
from src.core.lead_lookup import resolve_lead
from src.core.message_processor import process_message
from src.leads.models import LeadState

logger = logging.getLogger(__name__)

router = APIRouter()

# WhatsApp Business API integration (not yet configured)
# Requires: WhatsApp Business Account + Meta Developer setup
# See: https://developers.facebook.com/docs/whatsapp/business-api/
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "dentalflow_verify_token")

_response_store: dict[str, list[dict]] = {}


class WhatsAppOutgoingAdapter:
    def __init__(self, phone_number: str) -> None:
        self._phone = phone_number

    async def send_message(self, channel_user_id: str, text: str) -> None:
        phone = channel_user_id or self._phone
        _response_store.setdefault(phone, [])
        _response_store[phone].append({"role": "assistant", "text": text})
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

    messages = _response_store.get(body.phone_number, [])
    reply = messages[-1]["text"] if messages else ""
    return {"reply": reply}


@router.get("/whatsapp/webhook")
async def whatsapp_verify(hub_mode: str = "", hub_verify_token: str = "", hub_challenge: str = "") -> dict | str:
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified")
        return hub_challenge
    logger.warning("WhatsApp webhook verification failed: mode=%s, token=%s", hub_mode, hub_verify_token)
    return {"error": "verification failed"}


@router.get("/whatsapp/webhook/{phone_number}/messages")
async def get_messages(phone_number: str) -> dict:
    return {"messages": _response_store.get(phone_number, [])}