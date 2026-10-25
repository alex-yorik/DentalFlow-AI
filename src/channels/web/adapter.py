import hashlib
import logging
from pathlib import Path
from typing import cast

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from src.channels.base import IncomingMessage
from src.core.lead_lookup import resolve_lead
from src.core.message_processor import _MAX_INPUT_LENGTH, process_message
from src.leads.models import Lead

logger = logging.getLogger(__name__)

router = APIRouter()


class WebOutgoingAdapter:
    def __init__(self, channel_id: str) -> None:
        self._channel_id = channel_id
        self.sent: list[str] = []

    async def send_message(self, channel_user_id: str, text: str) -> None:
        self.sent.append(text)


class ChatRequest(BaseModel):
    channel_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_\-]+$",
    )
    text: str = Field(min_length=1, max_length=_MAX_INPUT_LENGTH)


def _channel_id_to_int(channel_id: str) -> int:
    return int(hashlib.sha256(channel_id.encode("utf-8")).hexdigest(), 16) & 0x7FFFFFFF


@router.post("/api/chat")
async def chat(request: Request, body: ChatRequest) -> dict:
    config = request.app.state.config
    llm_client = request.app.state.llm_client

    chat_id = _channel_id_to_int(body.channel_id)

    lead, blocked_reply = await resolve_lead(
        chat_id,
        source="web",
        channel_type="web",
        blocked_reply=config.client.business.messages.get("error_unsafe", ""),
    )
    if blocked_reply:
        return {"reply": blocked_reply}

    lead = cast(Lead, lead)

    msg = IncomingMessage(
        channel_user_id=body.channel_id,
        text=body.text,
        channel_type="web",
    )
    outgoing = WebOutgoingAdapter(body.channel_id)

    await process_message(
        msg=msg,
        outgoing=outgoing,
        lead=lead,
        config=config,
        llm_client=llm_client,
    )

    reply = outgoing.sent[-1] if outgoing.sent else ""
    return {"reply": reply}


@router.get("/")
async def chat_page() -> HTMLResponse:
    html_path = Path(__file__).parent / "templates" / "chat.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))