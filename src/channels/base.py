from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class IncomingMessage:
    channel_user_id: str
    text: str
    channel_type: str = "telegram"


@runtime_checkable
class OutgoingAdapter(Protocol):
    async def send_message(self, channel_user_id: str, text: str) -> None: ...