import pytest

from src.storage.conversation_repository import (
    append_message,
    get_recent_messages,
)


class TestConversationRepository:
    async def test_append_and_get_recent(self, db):
        await append_message(1, "user", "hello")
        await append_message(1, "assistant", "hi there")
        await append_message(1, "user", "book a cleaning")

        messages = await get_recent_messages(1)
        assert [m.text for m in messages] == ["hello", "hi there", "book a cleaning"]
        assert [m.role for m in messages] == ["user", "assistant", "user"]

    async def test_messages_isolated_per_user(self, db):
        await append_message(1, "user", "from chat 1")
        await append_message(2, "user", "from chat 2")

        assert [m.text for m in await get_recent_messages(1)] == ["from chat 1"]
        assert [m.text for m in await get_recent_messages(2)] == ["from chat 2"]

    async def test_limit(self, db):
        await append_message(1, "user", "m1")
        await append_message(1, "user", "m2")
        await append_message(1, "user", "m3")

        messages = await get_recent_messages(1, limit=2)
        assert [m.text for m in messages] == ["m2", "m3"]

    async def test_prunes_to_max_per_chat(self, db):
        for i in range(25):
            await append_message(1, "user", f"msg-{i}")

        messages = await get_recent_messages(1)
        assert len(messages) == 20
        assert messages[0].text == "msg-5"
        assert messages[-1].text == "msg-24"

    async def test_get_recent_empty(self, db):
        assert await get_recent_messages(999) == []
