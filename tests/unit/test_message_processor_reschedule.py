from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from src.core.message_processor import process_message
from src.channels.base import IncomingMessage
from src.leads.models import Lead, LeadState
from src.llm.contracts import AIOutput, ExtractedField, Intent, SuggestedAction
from src.storage.appointment_repository import (
    create_appointment,
    find_existing_appointment,
)
from src.storage.conversation_repository import get_recent_messages


class _RecorderClient:
    def __init__(self, output: AIOutput):
        self.output = output
        self.inputs = []

    async def analyze(self, ai_input):
        self.inputs.append(ai_input)
        return self.output


def _lead(chat_id=42, name="John", phone="555-0100", service="Cleaning"):
    now = datetime.now(timezone.utc)
    return Lead(
        id="lead-1", channel_user_id=chat_id, state=LeadState.COLLECT_FIELDS,
        name=name, phone=phone, service_interest=service,
        source="telegram", channel_type="telegram",
        created_at=now, updated_at=now,
    )


def _output(**kwargs):
    defaults = dict(
        intent=Intent.FAQ, confidence=0.95, reply_text="ok", is_lead=False,
        extracted_fields=[], missing_fields=[],
        suggested_action=SuggestedAction.CLOSE, safe=True,
        crm_write_allowed=False, schedule_followup=False,
        escalation_needed=False, is_fallback=False,
    )
    defaults.update(kwargs)
    return AIOutput(**defaults)


class _Outgoing:
    def __init__(self):
        self.sent = []
    async def send_message(self, channel_user_id, text):
        self.sent.append(text)


def _msg(text="hi"):
    return IncomingMessage(channel_user_id="42", text=text)


class TestDialogContext:
    async def test_records_user_and_assistant_messages(self, demo_app_config, db):
        lead = _lead()
        client = _RecorderClient(_output())
        await process_message(_msg("hello"), _Outgoing(), lead, demo_app_config, client)

        messages = await get_recent_messages(lead.channel_user_id)
        assert messages[0].role == "user"
        assert messages[0].text == "hello"
        assert messages[-1].role == "assistant"
        assert messages[-1].text == "ok"

    async def test_passes_previous_turns_as_recent_messages(self, demo_app_config, db):
        lead = _lead()
        first = _RecorderClient(_output(reply_text="first reply"))
        await process_message(_msg("first msg"), _Outgoing(), lead, demo_app_config, first)

        second = _RecorderClient(_output())
        await process_message(_msg("second msg"), _Outgoing(), lead, demo_app_config, second)

        recent = second.inputs[0].recent_messages
        texts = [m.text for m in recent]
        assert "first msg" in texts
        assert "first reply" in texts

    async def test_context_includes_known_fields(self, demo_app_config, db):
        lead = _lead()
        client = _RecorderClient(_output())
        await process_message(_msg("book"), _Outgoing(), lead, demo_app_config, client)
        assert "name=John" in client.inputs[0].conversation_context
        assert "phone=555-0100" in client.inputs[0].conversation_context

    async def test_missing_fields_guard_removes_known_fields(self, demo_app_config, db):
        lead = _lead(name="John", phone="555-0100", service=None)
        client = _RecorderClient(_output(
            missing_fields=["name", "phone", "service_interest"],
        ))
        await process_message(_msg("book cleaning"), _Outgoing(), lead, demo_app_config, client)

        assert "name" not in client.output.missing_fields
        assert "phone" not in client.output.missing_fields
        assert "service_interest" in client.output.missing_fields


class TestReschedule:
    async def test_lookup_not_called_on_regular_message(self, demo_app_config, db, monkeypatch):
        lead = _lead()
        client = _RecorderClient(_output())
        called = []

        async def fake_find(*args, **kwargs):
            called.append(args)
            return None

        monkeypatch.setattr("src.core.message_processor.find_existing_appointment", fake_find)
        await process_message(_msg("how much does cleaning cost"), _Outgoing(), lead, demo_app_config, client)

        assert called == []

    async def test_reschedule_asks_confirmation_without_changing(self, demo_app_config, db):
        lead = _lead(service=None)
        await create_appointment(lead, appointment_datetime="2026-08-10 10:00")
        out = _Outgoing()
        client = _RecorderClient(_output(
            intent=Intent.RESCHEDULE,
            suggested_action=SuggestedAction.RESCHEDULE,
            is_lead=True,
            extracted_fields=[ExtractedField(field_name="preferred_time", value="2026-08-11 09:00", confidence=0.95)],
        ))
        await process_message(_msg("bring it to 2026-08-11 09:00"), out, lead, demo_app_config, client)

        assert "Это ваша запись?" in out.sent[-1]
        found = await find_existing_appointment(name="John", phone="555-0100")
        assert found["appointment_datetime"] == "2026-08-10 10:00"

    async def test_reschedule_updates_appointment_datetime_after_confirmation(self, demo_app_config, db):
        lead = _lead(service=None)
        await create_appointment(lead, appointment_datetime="2026-08-10 10:00")
        out = _Outgoing()
        client = _RecorderClient(_output(
            intent=Intent.RESCHEDULE,
            suggested_action=SuggestedAction.RESCHEDULE,
            is_lead=True,
            extracted_fields=[ExtractedField(field_name="preferred_time", value="2026-08-11 09:00", confidence=0.95)],
        ))
        await process_message(_msg("bring it to 2026-08-11 09:00"), out, lead, demo_app_config, client)
        assert "Это ваша запись?" in out.sent[-1]

        client2 = _RecorderClient(_output(
            intent=Intent.RESCHEDULE,
            suggested_action=SuggestedAction.RESCHEDULE,
            is_lead=True,
            extracted_fields=[ExtractedField(field_name="preferred_time", value="2026-08-11 09:00", confidence=0.95)],
        ))
        await process_message(_msg("yes, confirm"), _Outgoing(), lead, demo_app_config, client2)

        found = await find_existing_appointment(name="John", phone="555-0100")
        assert found["appointment_datetime"] == "2026-08-11 09:00"
