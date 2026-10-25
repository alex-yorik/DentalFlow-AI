import hashlib
import logging
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.channels.base import IncomingMessage
from src.core.lead_lookup import resolve_lead
from src.core.message_processor import process_message

logger = logging.getLogger(__name__)

router = APIRouter()

_response_store: dict[str, list[dict]] = {}


class WebOutgoingAdapter:
    def __init__(self, channel_id: str) -> None:
        self._channel_id = channel_id

    async def send_message(self, channel_user_id: str, text: str) -> None:
        _response_store.setdefault(channel_user_id, [])
        _response_store[channel_user_id].append({"role": "assistant", "text": text})


class ChatRequest(BaseModel):
    channel_id: str
    text: str


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

    messages = _response_store.get(body.channel_id, [])
    reply = messages[-1]["text"] if messages else ""
    return {"reply": reply}


@router.get("/api/chat/{channel_id}/messages")
async def get_messages(channel_id: str) -> dict:
    return {"messages": _response_store.get(channel_id, [])}


@router.get("/")
async def chat_page() -> HTMLResponse:
    html_path = Path(__file__).parent / "templates" / "chat.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))