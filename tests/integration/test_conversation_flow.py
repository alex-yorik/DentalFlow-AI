from unittest.mock import AsyncMock, MagicMock

import pytest

from src.config.loader import AppConfig, load_client_config
from src.llm.contracts import AIOutput, ExtractedField, Intent, SuggestedAction
from src.llm.client import LLMClient
from src.channels.telegram.handlers import start_command, handle_message
from src.leads.models import Lead, LeadState
from src.leads.repository import get_lead_by_chat_id, create_lead, update_lead
from src.leads.state_machine import apply_transition
from src.followup import FollowUpEngine
from tests.conftest import CLIENT_NAME


@pytest.fixture
def config():
    client_cfg = load_client_config(CLIENT_NAME)
    return AppConfig(
        telegram_bot_token="test_token",
        openai_api_key="test_key",
        client_name=CLIENT_NAME,
        client=client_cfg,
    )


@pytest.fixture
def mock_llm() -> LLMClient:
    client = MagicMock(spec=LLMClient)
    client.analyze = AsyncMock()
    return client


@pytest.fixture
def mock_update():
    u = MagicMock()
    u.message.reply_text = AsyncMock()
    u.effective_chat.id = 99999
    u.message.text = ""
    return u


@pytest.fixture
def mock_context(config, mock_llm):
    c = MagicMock()
    c.bot_data = {"config": config, "llm_client": mock_llm}
    return c


def _make_output(**kwargs) -> AIOutput:
    defaults = dict(
        intent=Intent.FAQ,
        confidence=0.95,
        reply_text="We are open Mon-Fri 8-5.",
        is_lead=False,
        extracted_fields=[],
        missing_fields=[],
        suggested_action=SuggestedAction.ANSWER_FAQ,
        safe=True,
        crm_write_allowed=False,
        schedule_followup=False,
        escalation_needed=False,
        is_fallback=False,
    )
    defaults.update(kwargs)
    return AIOutput(**defaults)


class TestStartCommand:
    async def test_replies_with_welcome(self, mock_update, mock_context):
        await start_command(mock_update, mock_context)
        mock_update.message.reply_text.assert_awaited_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Bright Smile Dental" in text or "Hello" in text

    async def test_welcome_from_config(self, mock_update, mock_context):
        config = mock_context.bot_data["config"]
        expected = config.client.business.messages["welcome"]
        await start_command(mock_update, mock_context)
        mock_update.message.reply_text.assert_awaited_with(expected)


class TestHandleMessage:
    async def test_faq_flow_creates_lead_and_replies(self, mock_update, mock_context, db):
        mock_update.message.text = "What are your hours?"
        mock_context.bot_data["llm_client"].analyze.return_value = _make_output()

        await handle_message(mock_update, mock_context)

        mock_update.message.reply_text.assert_awaited()
        reply_text = mock_update.message.reply_text.call_args[0][0]
        assert reply_text == "We are open Mon-Fri 8-5."

    async def test_lead_intent_changes_state(self, mock_update, mock_context, db):
        mock_update.message.text = "I want to book a cleaning"
        mock_context.bot_data["llm_client"].analyze.return_value = _make_output(
            intent=Intent.LEAD,
            is_lead=True,
            reply_text="I'd love to help! What's your name?",
            extracted_fields=[ExtractedField(field_name="service", value="Teeth Cleaning", confidence=0.95)],
            missing_fields=["name", "phone"],
            suggested_action=SuggestedAction.ASK_FIELD,
        )

        await handle_message(mock_update, mock_context)

        lead = await get_lead_by_chat_id(99999)
        assert lead is not None
        assert lead.state == LeadState.COLLECT_FIELDS
        assert lead.service_interest == "Teeth Cleaning"

        mock_update.message.reply_text.assert_awaited_with("I'd love to help! What's your name?")

    async def test_llm_fallback_uses_error_message(self, mock_update, mock_context, db):
        mock_update.message.text = "Hi"
        mock_context.bot_data["llm_client"].analyze.return_value = _make_output(
            intent=Intent.OFF_TOPIC,
            confidence=0.0,
            escalation_needed=True,
            escalation_reason="API error",
            suggested_action=SuggestedAction.CLOSE,
            is_fallback=True,
        )

        await handle_message(mock_update, mock_context)

        config = mock_context.bot_data["config"]
        expected = config.client.business.messages["error_generic"]
        mock_update.message.reply_text.assert_awaited_with(expected)

    async def test_safety_block_blocks_lead(self, mock_update, mock_context, db):
        mock_update.message.text = "How much does it cost?"
        mock_context.bot_data["llm_client"].analyze.return_value = _make_output(
            reply_text="The price is $100",
            suggested_action=SuggestedAction.ANSWER_FAQ,
        )

        await handle_message(mock_update, mock_context)

        config = mock_context.bot_data["config"]
        expected = config.client.business.messages["error_unsafe"]
        mock_update.message.reply_text.assert_awaited_with(expected)

    async def test_safety_block_with_escalation_blocks_lead_state(self, mock_update, mock_context, db):
        lead = await create_lead(99999)
        lead.refusal_count = 2
        await update_lead(lead)

        mock_update.message.text = "I need a diagnosis"
        mock_context.bot_data["llm_client"].analyze.return_value = _make_output(
            intent=Intent.UNSAFE,
            safe=False,
            reply_text="Based on your symptoms, you have a cavity.",
            suggested_action=SuggestedAction.BLOCK,
        )

        await handle_message(mock_update, mock_context)

        lead = await get_lead_by_chat_id(99999)
        assert lead is not None
        assert lead.state == LeadState.BLOCKED
        assert lead.refusal_count == 3

    async def test_validation_failure_uses_out_of_scope_message(self, mock_update, mock_context, db):
        mock_update.message.text = "Book me"
        mock_context.bot_data["llm_client"].analyze.return_value = _make_output(
            intent=Intent.LEAD,
            is_lead=True,
            suggested_action=SuggestedAction.CLOSE,
        )

        await handle_message(mock_update, mock_context)

        config = mock_context.bot_data["config"]
        expected = config.client.business.messages["error_out_of_scope"]
        mock_update.message.reply_text.assert_awaited_with(expected)

    async def test_blocked_lead_gets_no_processing(self, mock_update, mock_context, db):
        lead = await create_lead(telegram_chat_id=99999)
        apply_transition(lead, LeadState.BLOCKED)
        await update_lead(lead)

        mock_update.message.text = "Hello"

        await handle_message(mock_update, mock_context)

        config = mock_context.bot_data["config"]
        expected = config.client.business.messages["error_unsafe"]
        mock_update.message.reply_text.assert_awaited_with(expected)

    async def test_full_qualification_flow_creates_lead_to_crm(self, mock_update, mock_context, db):
        mock_update.message.text = "John Doe, 555-0100, booking a checkup"
        mock_context.bot_data["llm_client"].analyze.return_value = _make_output(
            intent=Intent.LEAD,
            is_lead=True,
            reply_text="Great, I'll register you now!",
            extracted_fields=[
                ExtractedField(field_name="name", value="John Doe", confidence=0.99),
                ExtractedField(field_name="phone", value="555-0100", confidence=0.99),
                ExtractedField(field_name="service", value="Checkup", confidence=0.99),
            ],
            missing_fields=[],
            suggested_action=SuggestedAction.QUALIFY,
        )

        await handle_message(mock_update, mock_context)

        lead = await get_lead_by_chat_id(99999)
        assert lead is not None
        assert lead.state == LeadState.CLOSED
        assert lead.name == "John Doe"
        assert lead.phone == "555-0100"
        assert lead.service_interest == "Checkup"
        assert lead.crm_contact_id is not None

        mock_update.message.reply_text.assert_awaited_with("Great, I'll register you now!")

    async def test_crm_write_with_schedule_followup_goes_to_followup_pending(self, mock_update, mock_context, db):
        mock_context.bot_data["followup_engine"] = FollowUpEngine(
            mock_context.bot_data["config"], MagicMock()
        )

        mock_update.message.text = "Jane, 555-0200, booking a cleaning"
        mock_context.bot_data["llm_client"].analyze.return_value = _make_output(
            intent=Intent.LEAD,
            is_lead=True,
            reply_text="I'm scheduling a follow-up!",
            extracted_fields=[
                ExtractedField(field_name="name", value="Jane", confidence=0.99),
                ExtractedField(field_name="phone", value="555-0200", confidence=0.99),
                ExtractedField(field_name="service", value="Cleaning", confidence=0.99),
            ],
            missing_fields=[],
            suggested_action=SuggestedAction.QUALIFY,
            schedule_followup=True,
        )

        await handle_message(mock_update, mock_context)

        lead = await get_lead_by_chat_id(99999)
        assert lead is not None
        assert lead.state == LeadState.FOLLOWUP_PENDING, (
            "lead should transition to FOLLOWUP_PENDING when schedule_followup=True"
        )
        assert lead.crm_contact_id is not None
        assert lead.followup_task_id is not None