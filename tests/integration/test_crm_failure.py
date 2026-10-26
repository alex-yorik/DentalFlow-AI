from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.channels.telegram.handlers import handle_message
from src.config.loader import AppConfig, load_client_config
from src.followup import FollowUpEngine
from src.leads.models import LeadState
from src.leads.repository import create_lead, get_lead_by_chat_id, update_lead
from src.leads.state_machine import apply_transition
from src.llm.client import LLMClient
from src.llm.contracts import AIOutput, Intent, SuggestedAction
from tests.conftest import CLIENT_NAME

_CHAT_ID = 88800


def _next_chat_id():
    global _CHAT_ID
    _CHAT_ID += 1
    return _CHAT_ID


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
    u.effective_chat.id = _next_chat_id()
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
        reply_text="OK",
        is_lead=False,
        extracted_fields=[],
        missing_fields=[],
        suggested_action=SuggestedAction.ANSWER_FAQ,
        safe=True,
        crm_write_allowed=False,
        schedule_followup=False,
        escalation_needed=False,
    )
    defaults.update(kwargs)
    return AIOutput(**defaults)


class TestCrmFailureRecovery:
    async def test_crm_write_failure_resets_lead_to_collect_fields(self, mock_update, mock_context, db):
        """Task 1: CRM failure must not leave lead stuck in CRM_WRITE."""
        chat_id = mock_update.effective_chat.id
        lead = await create_lead(chat_id)
        apply_transition(lead, LeadState.QUALIFYING)
        lead.name = "John"
        lead.phone = "555-0100"
        lead.service_interest = "Checkup"
        lead.qualification_score = 100
        await update_lead(lead)

        mock_update.message.text = "yes please"
        mock_context.bot_data["llm_client"].analyze.return_value = _make_output(
            intent=Intent.LEAD,
            is_lead=True,
            reply_text="Registering you...",
            extracted_fields=[],
            missing_fields=[],
            suggested_action=SuggestedAction.CRM_WRITE,
        )

        with patch("src.integrations.crm.get_provider") as mock_get_provider:
            mock_crm = MagicMock()
            mock_crm.create_contact = AsyncMock(side_effect=Exception("CRM unavailable"))
            mock_get_provider.return_value = mock_crm

            await handle_message(mock_update, mock_context)

        lead = await get_lead_by_chat_id(chat_id)
        assert lead is not None
        assert lead.state != LeadState.CRM_WRITE, (
            f"Lead should not remain in CRM_WRITE after CRM failure, got {lead.state.value}"
        )
        assert lead.crm_contact_id is None

    async def test_followup_pending_clears_task_id_in_db(self, mock_update, mock_context, db):
        """Task 2: followup_task_id must be cleared in DB before refetch."""
        chat_id = mock_update.effective_chat.id
        lead = await create_lead(chat_id)
        apply_transition(lead, LeadState.FOLLOWUP_PENDING)
        lead.followup_task_id = "task-123"
        await update_lead(lead)

        followup_engine = FollowUpEngine(mock_context.bot_data["config"], MagicMock())
        followup_engine.cancel_followup = AsyncMock()
        mock_context.bot_data["followup_engine"] = followup_engine

        mock_update.message.text = "I'm back"
        mock_context.bot_data["llm_client"].analyze.return_value = _make_output(
            intent=Intent.LEAD,
            is_lead=True,
            reply_text="Welcome back!",
            extracted_fields=[],
            missing_fields=["name", "phone"],
            suggested_action=SuggestedAction.ASK_FIELD,
        )

        await handle_message(mock_update, mock_context)

        lead = await get_lead_by_chat_id(chat_id)
        assert lead is not None
        assert lead.followup_task_id is None, (
            f"followup_task_id should be None after user returns, got {lead.followup_task_id}"
        )

    async def test_blocked_transition_logs_warning(self, mock_update, mock_context, db, caplog):
        """Task 3: blocked transitions must produce a warning log."""
        mock_update.message.text = "book me"
        mock_context.bot_data["llm_client"].analyze.return_value = _make_output(
            intent=Intent.LEAD,
            is_lead=True,
            reply_text="Let me process that",
            extracted_fields=[],
            missing_fields=[],
            suggested_action=SuggestedAction.CRM_WRITE,
        )

        await handle_message(mock_update, mock_context)

        assert any(
            "Transition blocked" in record.message
            for record in caplog.records
        ), "Expected a warning log for blocked transition"
