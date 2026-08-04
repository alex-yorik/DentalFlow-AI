from unittest.mock import AsyncMock, MagicMock

import pytest

from src.channels.telegram.handlers import handle_message
from src.config.loader import AppConfig, load_client_config
from src.llm.contracts import AIOutput, Intent, SuggestedAction
from tests.conftest import CLIENT_NAME


@pytest.fixture
def app_config():
    client_cfg = load_client_config(CLIENT_NAME)
    return AppConfig(
        telegram_bot_token="test_token",
        openai_api_key="test_key",
        client_name=CLIENT_NAME,
        client=client_cfg,
    )


@pytest.fixture
def mock_llm():
    client = MagicMock()
    client.analyze = AsyncMock()
    return client


def _make_output(**kwargs) -> AIOutput:
    defaults = {
        "intent": Intent.LEAD,
        "confidence": 0.9,
        "reply_text": "I understand you have a broken tooth. Could you tell me more?",
        "is_lead": True,
        "extracted_fields": [],
        "missing_fields": ["name", "phone"],
        "suggested_action": SuggestedAction.ASK_FIELD,
        "safe": True,
        "crm_write_allowed": False,
        "schedule_followup": False,
        "escalation_needed": False,
        "is_fallback": False,
    }
    defaults.update(kwargs)
    return AIOutput(**defaults)


class TestSoftFallback:
    async def test_symptom_message_gets_clarifying_question(self, app_config, mock_llm, db):
        update = MagicMock()
        update.message.reply_text = AsyncMock()
        update.effective_chat.id = 77777
        update.message.text = "My tooth has broken"
        context = MagicMock()
        context.bot_data = {
            "config": app_config,
            "llm_client": mock_llm,
            "followup_engine": None,
        }
        context.bot = AsyncMock()
        mock_llm.analyze.return_value = _make_output()

        await handle_message(update, context)

        reply = update.message.reply_text.call_args[0][0]
        assert "Could you tell me more" in reply
        assert "can't provide" not in reply.lower()
        assert "I'm sorry" not in reply

    async def test_short_vague_message_does_not_hard_refuse(self, app_config, mock_llm, db):
        update = MagicMock()
        update.message.reply_text = AsyncMock()
        update.effective_chat.id = 77778
        update.message.text = "hi"
        context = MagicMock()
        context.bot_data = {
            "config": app_config,
            "llm_client": mock_llm,
            "followup_engine": None,
        }
        context.bot = AsyncMock()
        mock_llm.analyze.return_value = _make_output(
            intent=Intent.FAQ,
            reply_text="Hello! How can I help you today?",
            is_lead=False,
            suggested_action=SuggestedAction.ANSWER_FAQ,
        )

        await handle_message(update, context)

        reply = update.message.reply_text.call_args[0][0]
        assert reply == "Hello! How can I help you today?"
