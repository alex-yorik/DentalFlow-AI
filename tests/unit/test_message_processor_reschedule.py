from datetime import UTC, datetime

from src.channels.base import IncomingMessage
from src.core.message_processor import process_message
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
    now = datetime.now(UTC)
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
    async def test_regular_message_does_not_touch_appointment(self, demo_app_config, db):
        lead = _lead(service=None)
        await create_appointment(lead, appointment_datetime="2026-08-10 10:00")
        client = _RecorderClient(_output())
        await process_message(_msg("how much does cleaning cost"), _Outgoing(), lead, demo_app_config, client)

        found = await find_existing_appointment(name="John", phone="555-0100")
        assert found["appointment_datetime"] == "2026-08-10 10:00"

    async def test_reschedule_without_phone_asks_for_phone(self, demo_app_config, db):
        lead = _lead(phone=None)
        out = _Outgoing()
        client = _RecorderClient(_output(
            intent=Intent.RESCHEDULE,
            suggested_action=SuggestedAction.RESCHEDULE,
            is_lead=False,
            extracted_fields=[ExtractedField(field_name="preferred_time", value="2026-08-11 09:00", confidence=0.95)],
        ))
        await process_message(_msg("move it to 2026-08-11 09:00"), out, lead, demo_app_config, client)

        expected = demo_app_config.client.business.messages["reschedule_ask_phone"]
        assert out.sent[-1] == expected
        assert "phone" in client.output.missing_fields

    async def test_reschedule_with_phone_and_slot_acknowledges_requested_move(self, demo_app_config, db):
        lead = _lead(service=None)
        await create_appointment(lead, appointment_datetime="2026-08-10 10:00")
        out = _Outgoing()
        client = _RecorderClient(_output(
            intent=Intent.RESCHEDULE,
            suggested_action=SuggestedAction.RESCHEDULE,
            is_lead=False,
            extracted_fields=[ExtractedField(field_name="preferred_time", value="2026-08-11 09:00", confidence=0.95)],
        ))
        await process_message(_msg("bring it to 2026-08-11 09:00"), out, lead, demo_app_config, client)

        expected = demo_app_config.client.business.messages["reschedule_ack"].replace(
            "{preferred_time}", "2026-08-11 09:00"
        )
        assert out.sent[-1] == expected
        assert "you'd like to move your appointment to 2026-08-11 09:00" in out.sent[-1]
        assert "current appointment" not in out.sent[-1]
        found = await find_existing_appointment(name="John", phone="555-0100")
        assert found["appointment_datetime"] == "2026-08-10 10:00"

    async def test_reschedule_live_sequence_phone_then_slot(self, demo_app_config, db):
        lead = _lead(phone=None)
        messages = demo_app_config.client.business.messages
        out = _Outgoing()

        first = _RecorderClient(_output(
            intent=Intent.RESCHEDULE,
            suggested_action=SuggestedAction.RESCHEDULE,
            is_lead=False,
        ))
        await process_message(_msg("I want to reschedule"), out, lead, demo_app_config, first)
        assert out.sent[-1] == messages["reschedule_ask_phone"]

        second = _RecorderClient(_output(
            intent=Intent.RESCHEDULE,
            suggested_action=SuggestedAction.RESCHEDULE,
            is_lead=False,
            extracted_fields=[ExtractedField(field_name="phone", value="555-0100", confidence=0.95)],
        ))
        await process_message(_msg("+1 555 0100"), out, lead, demo_app_config, second)
        assert out.sent[-1] == messages["reschedule_ask_time"]

        third = _RecorderClient(_output(
            intent=Intent.RESCHEDULE,
            suggested_action=SuggestedAction.RESCHEDULE,
            is_lead=False,
            extracted_fields=[ExtractedField(field_name="preferred_time", value="2026-08-11 09:00", confidence=0.95)],
        ))
        await process_message(_msg("2026-08-11 09:00"), out, lead, demo_app_config, third)
        assert "you'd like to move your appointment to 2026-08-11 09:00" in out.sent[-1]

    async def test_new_reschedule_does_not_reuse_stale_preferred_time(self, demo_app_config, db):
        lead = _lead()
        lead.preferred_time = "2026-08-10 10:00"
        out = _Outgoing()
        client = _RecorderClient(_output(
            intent=Intent.RESCHEDULE,
            suggested_action=SuggestedAction.RESCHEDULE,
            is_lead=False,
        ))
        await process_message(_msg("I need to reschedule"), out, lead, demo_app_config, client)

        assert out.sent[-1] == demo_app_config.client.business.messages["reschedule_ask_time"]
