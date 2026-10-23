from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.channels.telegram.handlers import _extract_text_after_start, start_command


class TestExtractTextAfterStart:
    @pytest.mark.asyncio
    async def test_newline_trailing_text(self):
        assert _extract_text_after_start("/start\nMy tooth has broken") == "My tooth has broken"

    @pytest.mark.asyncio
    async def test_multi_line_text(self):
        raw = "/start\nMy tooth has broken, schedule today at 3pm\nMy name is John +1234567890"
        expected = "My tooth has broken, schedule today at 3pm\nMy name is John +1234567890"
        assert _extract_text_after_start(raw) == expected

    @pytest.mark.asyncio
    async def test_inline_args_and_text(self):
        assert _extract_text_after_start("/start token\nHi there") == "token\nHi there"

    @pytest.mark.asyncio
    async def test_only_command_returns_none(self):
        assert _extract_text_after_start("/start") is None
        assert _extract_text_after_start("/start ") is None

    @pytest.mark.asyncio
    async def test_empty_input_returns_none(self):
        assert _extract_text_after_start(None) is None
        assert _extract_text_after_start("") is None

    @pytest.mark.asyncio
    async def test_other_command_returns_none(self):
        assert _extract_text_after_start("/foo bar") is None


class TestStartCommandTrailingText:
    def _make_ctx(self):
        context = MagicMock()
        context.bot_data = {"config": MagicMock(), "llm_client": MagicMock()}
        context.bot_data["config"].client.business.messages.get.return_value = "Hello!"
        return context

    @pytest.mark.asyncio
    async def test_start_with_text_processes_message(self):
        update = MagicMock()
        update.message.reply_text = AsyncMock()
        update.message.text = "/start\nMy tooth has broken\nMy name is John +1234567890"
        context = self._make_ctx()

        with patch("src.channels.telegram.handlers.handle_message", new=AsyncMock()) as hm:
            await start_command(update, context)

        assert update.message.text == "My tooth has broken\nMy name is John +1234567890"
        hm.assert_awaited_once_with(update, context)

    @pytest.mark.asyncio
    async def test_start_with_inline_text_processes_message(self):
        update = MagicMock()
        update.message.reply_text = AsyncMock()
        update.message.text = "/start I'm Petrov Petr +79990000011, I want to reschedule"
        context = self._make_ctx()

        with patch("src.channels.telegram.handlers.handle_message", new=AsyncMock()) as hm:
            await start_command(update, context)

        assert update.message.text == "I'm Petrov Petr +79990000011, I want to reschedule"
        hm.assert_awaited_once_with(update, context)
        update.message.reply_text.assert_awaited_once_with("Hello!")

    @pytest.mark.asyncio
    async def test_start_without_text_only_welcomes(self):
        update = MagicMock()
        update.message.reply_text = AsyncMock()
        update.message.text = "/start"
        context = self._make_ctx()

        with patch("src.channels.telegram.handlers.handle_message", new=AsyncMock()) as hm:
            await start_command(update, context)

        hm.assert_not_awaited()
