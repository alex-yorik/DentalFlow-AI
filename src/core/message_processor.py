import logging
from datetime import datetime, timezone

from src.config.loader import AppConfig, QualificationConfig
from src.llm.contracts import AIInput
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


def build_context(lead: Lead) -> str:
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
    return "; ".join(parts)


def apply_extracted_fields(lead: Lead, output, user_message: str, reply_text: str) -> None:
    for field in output.extracted_fields:
        if field.confidence < 0.5:
            continue
        lead_field = _field_map.get(field.field_name)
        if lead_field and getattr(lead, lead_field, None) is None:
            if field.field_name == 'phone' and not PHONE_PATTERN.match(field.value):
                logger.warning(f"LLM extracted invalid phone format: {field.value}")
            elif field.field_name == 'email' and not EMAIL_PATTERN.match(field.value):
                logger.warning(f"LLM extracted invalid email format: {field.value}")
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
    from src.channels.telegram.handlers import get_provider
    crm = get_provider(config.crm_provider)
    try:
        contact_id = await crm.create_contact(lead)
        lead.crm_contact_id = contact_id
        lead_id = await crm.create_lead(contact_id, lead)
        await crm.add_note(lead_id, f"Lead from {lead.channel_type}: {lead.conversation_summary[:200]}")
        await crm.update_stage(lead_id, "new")
        await notify_staff(config, lead, bot_for_notifications)

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
        logger.error("CRM write failed for lead %s (chat %s): %s", lead.id, lead.telegram_chat_id, e)
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
        await outgoing.send_message(
            msg.channel_user_id,
            config.client.business.messages.get("error_generic", ""),
        )
        return

    ai_input = AIInput(
        system_prompt=config.client.prompts.system,
        user_message=user_text,
        conversation_context=build_context(lead),
    )

    output = await llm_client.analyze(ai_input)

    if output.escalation_needed and output.is_fallback:
        logger.warning("LLM fallback for %s %s: %s", msg.channel_type, msg.channel_user_id, output.escalation_reason)
        await outgoing.send_message(
            msg.channel_user_id,
            config.client.business.messages.get("error_generic", ""),
        )
        return

    validation = validate_ai_output(output, config.client.rules)
    if not validation.valid:
        logger.warning("Validation failed for %s %s: %s", msg.channel_type, msg.channel_user_id, validation.reason)
        await outgoing.send_message(
            msg.channel_user_id,
            config.client.business.messages.get("error_out_of_scope", ""),
        )
        return

    verdict = check_safety(output, config.client.rules, lead)
    if not verdict.allowed:
        logger.warning("Safety check failed for %s %s: %s", msg.channel_type, msg.channel_user_id, verdict.blocked_reason)
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
    await outgoing.send_message(msg.channel_user_id, output.reply_text)