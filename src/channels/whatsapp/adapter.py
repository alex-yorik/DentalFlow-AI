import hashlib
import logging
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from src.channels.base import IncomingMessage, OutgoingAdapter
from src.core.message_processor import process_message
from src.leads.models import LeadState
from src.leads.repository import get_lead_by_chat_id, create_lead

logger = logging.getLogger(__name__)

router = APIRouter()

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

    lead = await get_lead_by_chat_id(chat_id)
    if lead and lead.state == LeadState.BLOCKED:
        return {"reply": config.client.business.messages.get("error_unsafe", "")}
    if lead and lead.state == LeadState.CLOSED:
        lead = None
    if lead is None:
        lead = await create_lead(chat_id, source="whatsapp", channel_type="whatsapp")

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
    expected_token = "dentalflow_verify_token"
    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        logger.info("WhatsApp webhook verified")
        return hub_challenge
    logger.warning("WhatsApp webhook verification failed: mode=%s, token=%s", hub_mode, hub_verify_token)
    return {"error": "verification failed"}


@router.get("/whatsapp/webhook/{phone_number}/messages")
async def get_messages(phone_number: str) -> dict:
    return {"messages": _response_store.get(phone_number, [])}