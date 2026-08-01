import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes

from src.config.loader import AppConfig, QualificationConfig
from src.llm.contracts import AIInput
from src.llm.client import LLMClient
from src.rules.validator import validate_ai_output
from src.rules.safety import check_safety
from src.rules.qualification import calculate_score
from src.leads.models import Lead, LeadState
from src.leads.repository import create_lead, get_lead_by_chat_id, update_lead
from src.leads.state_machine import suggest_state, validate_transition, apply_transition
from src.integrations.crm import get_provider
from src.integrations.notifications import notify_staff
from src.followup import FollowUpEngine
from src.storage import database

logger = logging.getLogger(__name__)

_MAX_INPUT_LENGTH = 2000

_RATE_LIMIT_MAX = 10
_RATE_LIMIT_WINDOW = 60.0

_field_map = {
    "name": "name",
    "phone": "phone",
    "email": "email",
    "service": "service_interest",
    "urgency": "urgency",
    "preferred_time": "preferred_time",
}


def _sanitize_input(text: str | None) -> str | None:
    if not text:
        return None
    stripped = text.strip()
    if not stripped:
        return None
    return stripped[:_MAX_INPUT_LENGTH]


def _build_context(lead: Lead) -> str:
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


def _apply_extracted_fields(lead: Lead, output, user_message: str, reply_text: str) -> None:
    for field in output.extracted_fields:
        if field.confidence < 0.5:
            continue
        lead_field = _field_map.get(field.field_name)
        if lead_field and getattr(lead, lead_field, None) is None:
            setattr(lead, lead_field, field.value)

    new_entry = f"User asked about {output.intent.value}"
    prev = lead.conversation_summary
    lead.conversation_summary = f"{prev}; {new_entry}" if prev else new_entry
    if lead.conversation_summary:
        lead.conversation_summary = lead.conversation_summary[:500]


def _try_advance_lead(lead: Lead, qual_config: QualificationConfig) -> None:
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


async def _write_to_crm(lead: Lead, config: AppConfig, bot, schedule_followup: bool = False, followup_engine: FollowUpEngine | None = None) -> None:
    if lead.crm_contact_id:
        return
    crm = get_provider(config.crm_provider)
    try:
        contact_id = await crm.create_contact(lead)
        lead.crm_contact_id = contact_id
        lead_id = await crm.create_lead(contact_id, lead)
        await crm.add_note(lead_id, f"Lead from Telegram: {lead.conversation_summary[:200]}")
        await crm.update_stage(lead_id, "new")
        await notify_staff(config, lead, bot)

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


_rate_limit: dict[int, deque] = defaultdict(deque)


def _check_rate_limit(chat_id: int) -> bool:
    now = time.monotonic()
    timestamps = _rate_limit[chat_id]
    while timestamps and timestamps[0] < now - _RATE_LIMIT_WINDOW:
        timestamps.popleft()
    if len(timestamps) >= _RATE_LIMIT_MAX:
        return False
    timestamps.append(now)
    return True


_RATE_LIMIT_REPLY = "Please slow down. You are sending messages too quickly."


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config: AppConfig = context.bot_data["config"]
    text = config.client.business.messages.get("welcome", "Hello!")
    await update.message.reply_text(text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config: AppConfig = context.bot_data["config"]
    llm_client: LLMClient = context.bot_data["llm_client"]
    chat_id = update.effective_chat.id

    user_text = _sanitize_input(update.message.text)
    if user_text is None:
        await update.message.reply_text(
            config.client.business.messages.get("error_generic", "")
        )
        return

    if not _check_rate_limit(chat_id):
        logger.warning("Rate limit hit for chat %s", chat_id)
        await update.message.reply_text(_RATE_LIMIT_REPLY)
        return

    lead = await get_lead_by_chat_id(chat_id)

    if lead and lead.state == LeadState.BLOCKED:
        await update.message.reply_text(
            config.client.business.messages.get("error_unsafe", "")
        )
        return

    if lead and lead.state == LeadState.FOLLOWUP_PENDING:
        followup_engine = context.bot_data.get("followup_engine")
        if followup_engine:
            await followup_engine.cancel_followup(lead.id)
        now = datetime.now(timezone.utc)
        conn = await database.get_connection()
        await conn.execute(
            "UPDATE leads SET followup_task_id = NULL, updated_at = ? WHERE id = ?",
            (now.isoformat(), lead.id),
        )
        await conn.commit()
        await conn.close()
        lead = await get_lead_by_chat_id(chat_id)

    if lead and lead.state == LeadState.CLOSED:
        lead = None

    if lead is None:
        lead = await create_lead(chat_id)

    ai_input = AIInput(
        system_prompt=config.client.prompts.system,
        user_message=user_text,
        conversation_context=_build_context(lead),
    )

    output = await llm_client.analyze(ai_input)

    if output.escalation_needed and output.is_fallback:
        logger.warning("LLM fallback for chat %s: %s", chat_id, output.escalation_reason)
        await update.message.reply_text(
            config.client.business.messages.get("error_generic", "")
        )
        return

    validation = validate_ai_output(output, config.client.rules)
    if not validation.valid:
        logger.warning("Validation failed for chat %s: %s", chat_id, validation.reason)
        await update.message.reply_text(
            config.client.business.messages.get("error_out_of_scope", "")
        )
        return

    verdict = check_safety(output, config.client.rules, lead)
    if not verdict.allowed:
        logger.warning("Safety check failed for chat %s: %s", chat_id, verdict.blocked_reason)
        await update.message.reply_text(
            config.client.business.messages.get("error_unsafe", "")
        )
        if verdict.escalate:
            t = validate_transition(lead.state, LeadState.BLOCKED)
            if t.allowed:
                apply_transition(lead, LeadState.BLOCKED)
        await update_lead(lead)
        return

    _apply_extracted_fields(lead, output, user_text, output.reply_text)

    if output.is_lead and lead.state == LeadState.NEW:
        t = validate_transition(LeadState.NEW, LeadState.COLLECT_FIELDS)
        if t.allowed:
            apply_transition(lead, LeadState.COLLECT_FIELDS)

    next_state = suggest_state(output.suggested_action)
    transition = validate_transition(lead.state, next_state, lead, config.client.qualification)

    if transition.allowed:
        apply_transition(lead, next_state)

        if next_state == LeadState.CRM_WRITE:
            followup_engine = context.bot_data.get("followup_engine")
            await _write_to_crm(lead, config, context.bot, output.schedule_followup, followup_engine)
    else:
        logger.warning(
            "Transition blocked for chat %s: %s → %s — %s",
            chat_id, lead.state.value, next_state.value, transition.reason,
        )

    _try_advance_lead(lead, config.client.qualification)

    if lead.state == LeadState.CRM_WRITE:
        followup_engine = context.bot_data.get("followup_engine")
        await _write_to_crm(lead, config, context.bot, output.schedule_followup, followup_engine)

    await update_lead(lead)
    await update.message.reply_text(output.reply_text)