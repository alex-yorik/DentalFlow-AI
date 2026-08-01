from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from src.config.loader import AppConfig, ClientConfig, BusinessInfo, Service, FAQItem, RulesConfig, QualificationConfig, FollowUpConfig, PromptCollection
from src.integrations.notifications import notify_staff_followup_complete
from src.leads.models import Lead, LeadState


def _make_config(staff_chat_id: int = 123456789) -> AppConfig:
    return AppConfig(
        telegram_bot_token="test_token",
        openai_api_key="test_key",
        client_name="test_clinic",
        client=ClientConfig(
            business=BusinessInfo(
                name="Test Clinic",
                address="123 Main St",
                phone="+1234567890",
                hours={"Mon-Fri": "9:00-18:00"},
                timezone="America/New_York",
                staff_chat_id=staff_chat_id,
                messages={"welcome": "Hello"},
            ),
            services=[],
            faq=[],
            rules=RulesConfig(blocked_phrases=[], confidence_threshold=0.5, max_refusal_count=3),
            qualification=QualificationConfig(critical_fields=[], score_rules={}, crm_write_threshold=0),
            followup=FollowUpConfig(templates={}, delay_minutes=60, max_retries=2, poll_interval_seconds=30),
            prompts=PromptCollection(system="test"),
        ),
    )


def _make_lead(**overrides) -> Lead:
    defaults = dict(
        id="1",
        telegram_chat_id=12345,
        state=LeadState.FOLLOWUP_PENDING,
        name="Test User",
        phone="+1234567890",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    defaults.update(overrides)
    return Lead(**defaults)


@pytest.mark.asyncio
async def test_notify_staff_followup_complete():
    config = _make_config(staff_chat_id=999)
    bot = AsyncMock()
    lead = _make_lead()

    await notify_staff_followup_complete(config, lead, bot)

    bot.send_message.assert_awaited_once_with(
        chat_id=999,
        text=f"Follow-up completed for lead {lead.id} (chat {lead.telegram_chat_id})",
    )


@pytest.mark.asyncio
async def test_notify_staff_followup_complete_error_handling():
    config = _make_config(staff_chat_id=999)
    bot = AsyncMock()
    bot.send_message.side_effect = Exception("Telegram API error")
    lead = _make_lead()

    await notify_staff_followup_complete(config, lead, bot)

    bot.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_notify_staff_followup_complete_skips_when_no_chat_id():
    config = _make_config(staff_chat_id=0)
    bot = AsyncMock()
    lead = _make_lead()

    await notify_staff_followup_complete(config, lead, bot)

    bot.send_message.assert_not_awaited()