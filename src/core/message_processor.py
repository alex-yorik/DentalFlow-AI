import logging
from datetime import datetime, timezone

from src.config.loader import AppConfig, QualificationConfig
from src.llm.contracts import AIInput, Intent
from src.llm.client import LLMClient
from src.rules.validator import validate_ai_output
from src.rules.safety import check_safety
from src.rules.qualification import calculate_score
from src.leads.models import Lead, LeadState, PHONE_PATTERN, EMAIL_PATTERN
from src.leads.repository import update_lead
from src.leads.state_machine import suggest_state, validate_transition, apply_transition
from src.integrations.notifications import notify_staff
from src.channels.base import IncomingMessage, OutgoingAdapter
from src.followup import FollowUpEngine
from src.monitoring.metrics import metrics
from src.storage.conversation_repository import append_message, get_recent_messages
from src.storage.appointment_repository import (
    find_existing_appointment,
    create_appointment,
    update_appointment_datetime,
)

logger = logging.getLogger(__name__)

_MAX_INPUT_LENGTH = 2000

_field_map = {
    "name": "name",
    "phone": "phone",
    "email": "email",
    "service": "service_interest",
    "urgency": "urgency",
    "preferred_time": "preferred_time",
}


def sanitize_input(text: str | None) -> str | None:
    if not text:
        return None
    stripped = text.strip()
    if not stripped:
        return None
    return stripped[:_MAX_INPUT_LENGTH]


def build_context(lead: Lead, existing_appointment: dict | None = None) -> str:
    known = []
    for src, dst in _field_map.items():
        val = getattr(lead, dst, None)
        if val:
            known.append(f"{src}={val}")
    parts = [f"State: {lead.state.value}"]
    if known:
        parts.append(f"Known: {', '.join(known)}")
    if lead.conversation_summary:
        parts.append(f"Summary: {lead.conversation_summary}")
    if existing_appointment:
        when = existing_appointment.get("appointment_datetime") or "unspecified"
        service = existing_appointment.get("service") or ""
        parts.append(
            f"Existing appointment: {service} on {when} — user asked to reschedule; confirm the change and ask for the new date/time"
        )
    return "; ".join(parts)


def _known_missing(lead: Lead, field: str) -> bool:
    mapping = {
        "name": "name",
        "phone": "phone",
        "email": "email",
        "service": "service_interest",
        "service_interest": "service_interest",
        "preferred_time": "preferred_time",
    }
    attr = mapping.get(field)
    return bool(attr and getattr(lead, attr, None))


def _build_confirmation_reply(appointment: dict, new_time: str) -> str:
    service = appointment.get("service") or "запись"
    when = appointment.get("appointment_datetime") or "уточнённое время"
    return (
        f"У вас есть запись на {service} на {when}. "
        f"Это ваша запись? Подтвердите перенос на {new_time}."
    )


def _confirmation_pending(recent_messages, appointment: dict) -> bool:
    if not recent_messages:
        return False
    last = recent_messages[-1]
    if getattr(last, "role", None) != "assistant":
        return False
    service = appointment.get("service") or "запись"
    when = appointment.get("appointment_datetime") or "уточнённое время"
    marker = f"У вас есть запись на {service} на {when}."
    return marker in getattr(last, "text", "")


def apply_extracted_fields(lead: Lead, output, user_message: str, reply_text: str) -> None:
    for field in output.extracted_fields:
        if field.confidence < 0.5:
            continue
        lead_field = _field_map.get(field.field_name)
        if lead_field and getattr(lead, lead_field, None) is None:
            if field.field_name == 'phone' and not PHONE_PATTERN.match(field.value):
                logger.warning(f"LLM extracted invalid phone format: {field.value}")
                continue
            elif field.field_name == 'email' and not EMAIL_PATTERN.match(field.value):
                logger.warning(f"LLM extracted invalid email format: {field.value}")
                continue
            setattr(lead, lead_field, field.value)

    new_entry = f"User asked about {output.intent.value}"
    prev = lead.conversation_summary
    lead.conversation_summary = f"{prev}; {new_entry}" if prev else new_entry
    if lead.conversation_summary:
        lead.conversation_summary = lead.conversation_summary[:500]


def try_advance_lead(lead: Lead, qual_config: QualificationConfig) -> None:
    if lead.state == LeadState.COLLECT_FIELDS:
        if not all(getattr(lead, f, None) for f in qual_config.critical_fields):
            return

        t = validate_transition(LeadState.COLLECT_FIELDS, LeadState.QUALIFYING, lead, qual_config)
        if not t.allowed:
            return

        apply_transition(lead, LeadState.QUALIFYING)

    if lead.state == LeadState.QUALIFYING:
        qual = calculate_score(lead, qual_config)
        lead.qualification_score = qual.score

        t = validate_transition(LeadState.QUALIFYING, LeadState.CRM_WRITE, lead, qual_config)
        if t.allowed:
            apply_transition(lead, LeadState.CRM_WRITE)


async def _write_to_crm(lead: Lead, config: AppConfig, bot_for_notifications, schedule_followup: bool = False, followup_engine: FollowUpEngine | None = None) -> None:
    if lead.crm_contact_id:
        return
    from src.integrations.crm import get_provider
    crm = get_provider(config.crm_provider)
    try:
        contact_id = await crm.create_contact(lead)
        lead.crm_contact_id = contact_id
        lead_id = await crm.create_lead(contact_id, lead)
        await crm.add_note(lead_id, f"Lead from {lead.channel_type}: {lead.conversation_summary[:200]}")
        await crm.update_stage(lead_id, "new")
        await notify_staff(config, lead, bot_for_notifications)
        try:
            await create_appointment(lead)
        except Exception as e:
            logger.error("Failed to create appointment for lead %s: %s", lead.id, e)

        if schedule_followup and followup_engine:
            t = validate_transition(LeadState.CRM_WRITE, LeadState.FOLLOWUP_PENDING, lead, config.client.qualification)
            if t.allowed:
                apply_transition(lead, LeadState.FOLLOWUP_PENDING)
                await followup_engine.schedule_followup(lead)
            else:
                apply_transition(lead, LeadState.CLOSED)
        else:
            apply_transition(lead, LeadState.CLOSED)
    except Exception as e:
        logger.error("CRM write failed for lead %s (chat %s): %s", lead.id, lead.channel_user_id, e)
        lead.crm_contact_id = None
        apply_transition(lead, LeadState.COLLECT_FIELDS)


async def process_message(
    msg: IncomingMessage,
    outgoing: OutgoingAdapter,
    lead: Lead,
    config: AppConfig,
    llm_client: LLMClient,
    followup_engine: FollowUpEngine | None = None,
    bot_for_notifications=None,
) -> None:
    user_text = sanitize_input(msg.text)
    if user_text is None:
        metrics.inc("messages_processed")
        await outgoing.send_message(
            msg.channel_user_id,
            config.client.business.messages.get("error_generic", ""),
        )
        return

    recent_messages = await get_recent_messages(lead.channel_user_id, limit=10)
    await append_message(lead.channel_user_id, "user", user_text)

    ai_input = AIInput(
        system_prompt=config.client.prompts.system,
        user_message=user_text,
        conversation_context=build_context(lead),
        recent_messages=recent_messages,
    )

    output = await llm_client.analyze(ai_input)

    if output.escalation_needed and output.is_fallback:
        logger.warning("LLM fallback for %s %s: %s", msg.channel_type, msg.channel_user_id, output.escalation_reason)
        metrics.inc("messages_processed")
        metrics.inc("messages_error")
        await outgoing.send_message(
            msg.channel_user_id,
            config.client.business.messages.get("error_generic", ""),
        )
        return

    validation = validate_ai_output(output, config.client.rules)
    if not validation.valid:
        logger.warning("Validation failed for %s %s: %s", msg.channel_type, msg.channel_user_id, validation.reason)
        metrics.inc("messages_error")
        await outgoing.send_message(
            msg.channel_user_id,
            config.client.business.messages.get("error_out_of_scope", ""),
        )
        return

    verdict = check_safety(output, config.client.rules, lead)
    if not verdict.allowed:
        logger.warning("Safety check failed for %s %s: %s", msg.channel_type, msg.channel_user_id, verdict.blocked_reason)
        metrics.inc("messages_error")
        await outgoing.send_message(
            msg.channel_user_id,
            config.client.business.messages.get("error_unsafe", ""),
        )
        if verdict.escalate:
            t = validate_transition(lead.state, LeadState.BLOCKED)
            if t.allowed:
                apply_transition(lead, LeadState.BLOCKED)
        await update_lead(lead)
        return

    apply_extracted_fields(lead, output, user_text, output.reply_text)

    output.missing_fields = [f for f in output.missing_fields if not _known_missing(lead, f)]

    if output.intent == Intent.RESCHEDULE and lead.phone:
        existing_appointment = await find_existing_appointment(lead.name, lead.phone)
        new_time = lead.preferred_time
        if existing_appointment and new_time:
            if _confirmation_pending(recent_messages, existing_appointment):
                try:
                    await update_appointment_datetime(existing_appointment["id"], new_time)
                    logger.info("Rescheduled appointment %s for chat %s to %s", existing_appointment["id"], msg.channel_user_id, new_time)
                except Exception as e:
                    logger.error("Failed to update appointment %s: %s", existing_appointment["id"], e)
            else:
                output.reply_text = _build_confirmation_reply(existing_appointment, new_time)

    if output.is_lead and lead.state == LeadState.NEW:
        t = validate_transition(LeadState.NEW, LeadState.COLLECT_FIELDS)
        if t.allowed:
            apply_transition(lead, LeadState.COLLECT_FIELDS)

    next_state = suggest_state(output.suggested_action)
    transition = validate_transition(lead.state, next_state, lead, config.client.qualification)

    if transition.allowed:
        apply_transition(lead, next_state)
    else:
        logger.warning(
            "Transition blocked for %s %s: %s → %s — %s",
            msg.channel_type, msg.channel_user_id, lead.state.value, next_state.value, transition.reason,
        )

    try_advance_lead(lead, config.client.qualification)

    if lead.state == LeadState.CRM_WRITE:
        await _write_to_crm(lead, config, bot_for_notifications, output.schedule_followup, followup_engine)

    await update_lead(lead)
    metrics.inc("messages_processed")
    await outgoing.send_message(msg.channel_user_id, output.reply_text)
    try:
        await append_message(lead.channel_user_id, "assistant", output.reply_text)
    except Exception as e:
        logger.error("Failed to record assistant message for chat %s: %s", msg.channel_user_id, e)