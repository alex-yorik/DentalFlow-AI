import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.followup import FollowUpEngine, _acquire_task, _cancel_tasks_by_lead, _get_due_tasks, _insert_task
from src.followup.models import FollowUpTask
from src.leads.models import LeadState
from src.leads.repository import create_lead, get_lead_by_chat_id, update_lead
from src.leads.state_machine import apply_transition
from src.storage.appointment_repository import create_appointment


def _make_task(lead_id: str, chat_id: int, **overrides) -> FollowUpTask:
    now = datetime.now(UTC)
    defaults = {
        "id": str(uuid.uuid4()),
        "lead_id": lead_id,
        "chat_id": chat_id,
        "retry_count": 0,
        "max_retries": 2,
        "next_run_at": now,
        "status": "pending",
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return FollowUpTask(**defaults)


def _make_engine_config(overrides: dict | None = None) -> MagicMock:
    config = MagicMock()
    config.client.followup.poll_interval_seconds = 30
    config.client.followup.delay_minutes = 60
    config.client.followup.max_retries = 2
    config.client.followup.templates = {
        "initial": "Test initial {name} {service_interest}",
        "existing_appointment": "Test existing {name}",
        "reminder": "Test reminder",
        "final": "Test final",
    }
    config.client.business.staff_chat_id = 0
    if overrides:
        for k, v in overrides.items():
            setattr(config.client.followup, k, v)
    return config


# ─── Basic unit tests ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_acquire_task_claims_only_once(db):
    task_id = str(uuid.uuid4())
    now = datetime.now(UTC)
    task = _make_task("lead-1", 100, id=task_id, next_run_at=now)
    await _insert_task(task)

    acquired1 = await _acquire_task(task_id)
    assert acquired1 is True

    acquired2 = await _acquire_task(task_id)
    assert acquired2 is False


@pytest.mark.asyncio
async def test_acquire_task_skips_non_pending(db):
    task_id = str(uuid.uuid4())
    now = datetime.now(UTC)
    task = _make_task("lead-2", 200, id=task_id, next_run_at=now, status="completed")
    await _insert_task(task)

    acquired = await _acquire_task(task_id)
    assert acquired is False


@pytest.mark.asyncio
async def test_acquire_task_unknown_id(db):
    acquired = await _acquire_task("nonexistent")
    assert acquired is False


@pytest.mark.asyncio
async def test_get_due_tasks_skips_acquired(db):
    task_id = str(uuid.uuid4())
    now = datetime.now(UTC)
    task = _make_task("lead-3", 300, id=task_id, next_run_at=now - timedelta(minutes=5), status="running")
    await _insert_task(task)

    due = await _get_due_tasks(now)
    assert task_id not in [t.id for t in due]


@pytest.mark.asyncio
async def test_cancel_followup_mid_cycle(db):
    task_id = str(uuid.uuid4())
    now = datetime.now(UTC)
    task = _make_task("lead-4", 400, id=task_id, next_run_at=now - timedelta(minutes=1))
    await _insert_task(task)

    await _cancel_tasks_by_lead("lead-4")

    due = await _get_due_tasks(now)
    assert task_id not in [t.id for t in due]


# ─── Poll interval config ────────────────────────────────────────────────────


def test_followup_poll_interval_config(demo_client_config):
    fu = demo_client_config.followup
    assert fu.poll_interval_seconds == 30


def test_followup_poll_interval_default():
    from src.config.loader import FollowUpConfig
    fu = FollowUpConfig(templates={"initial": "Hi"})
    assert fu.poll_interval_seconds == 30


# ─── CRITICAL 1: Reschedule pending recovery ─────────────────────────────────


@pytest.mark.asyncio
async def test_reschedule_pending_recovery(db):
    now = datetime.now(UTC)
    stale = _make_task("lead-s1", 500, next_run_at=now - timedelta(hours=2), retry_count=1)
    future = _make_task("lead-s2", 501, next_run_at=now + timedelta(hours=2), retry_count=1)
    await _insert_task(stale)
    await _insert_task(future)

    config = _make_engine_config()
    bot = MagicMock()
    engine = FollowUpEngine(config, bot)

    await engine._reschedule_pending()

    stale_updated = await _get_due_tasks(now + timedelta(minutes=2))
    stale_ids = [t.id for t in stale_updated]
    assert stale.id in stale_ids, "stale task should be rescheduled to ~now+1m"

    future_updated = await _get_due_tasks(now + timedelta(hours=3))
    future_ids = [t.id for t in future_updated]
    assert future.id in future_ids, "future task should remain unchanged"


# ─── CRITICAL 2: send_followup full cycle ────────────────────────────────────


@pytest.mark.asyncio
async def test_send_followup_full_cycle_reschedule(db):
    lead = await create_lead(500)
    apply_transition(lead, LeadState.FOLLOWUP_PENDING)
    await update_lead(lead)

    now = datetime.now(UTC)
    task = _make_task(
        lead.id,
        lead.channel_user_id,
        next_run_at=now - timedelta(minutes=5),
        retry_count=0,
        max_retries=2,
    )
    await _insert_task(task)

    config = _make_engine_config()
    bot = MagicMock()
    bot.send_message = AsyncMock()
    engine = FollowUpEngine(config, bot)

    await engine._send_followup(task)

    bot.send_message.assert_awaited_once()
    assert bot.send_message.call_args[1]["chat_id"] == lead.channel_user_id

    updated = await _get_due_tasks(datetime.now(UTC) + timedelta(minutes=61))
    task_updated = next((t for t in updated if t.id == task.id), None)
    assert task_updated is not None, "task should be rescheduled with future next_run_at"
    assert task_updated.retry_count == 1, "retry_count should be incremented"
    assert task_updated.status == "pending", "task status should be reset to pending"
    assert task_updated.next_run_at > now, "next_run_at should be in the future"


@pytest.mark.asyncio
async def test_send_followup_full_cycle_complete(db):
    lead = await create_lead(501)
    apply_transition(lead, LeadState.FOLLOWUP_PENDING)
    await update_lead(lead)

    now = datetime.now(UTC)
    task = _make_task(
        lead.id,
        lead.channel_user_id,
        next_run_at=now - timedelta(minutes=5),
        retry_count=0,
        max_retries=1,
    )
    await _insert_task(task)

    config = _make_engine_config(overrides={"max_retries": 1})
    bot = MagicMock()
    bot.send_message = AsyncMock()
    engine = FollowUpEngine(config, bot)

    await engine._send_followup(task)

    bot.send_message.assert_awaited_once()

    due = await _get_due_tasks(datetime.now(UTC) + timedelta(hours=1))
    assert task.id not in [t.id for t in due], "completed task should not be due"

    lead_updated = await get_lead_by_chat_id(lead.channel_user_id)
    assert lead_updated.state == LeadState.CLOSED, "lead should be closed after max retries"


@pytest.mark.asyncio
async def test_get_template_existing_appointment_initial():
    config = _make_engine_config()
    engine = FollowUpEngine(config, MagicMock())
    initial = engine._get_template(config.client.followup, 0, has_appointment=False)
    existing = engine._get_template(config.client.followup, 0, has_appointment=True)
    assert initial == "Test initial {name} {service_interest}"
    assert existing == "Test existing {name}"
    assert initial != existing


@pytest.mark.asyncio
async def test_send_followup_uses_existing_appointment_template(db):
    lead = await create_lead(504)
    lead.name = "John"
    lead.phone = "555-0000"
    lead.service_interest = "Cleaning"
    apply_transition(lead, LeadState.FOLLOWUP_PENDING)
    await update_lead(lead)
    await create_appointment(lead)

    now = datetime.now(UTC)
    task = _make_task(
        lead.id,
        lead.channel_user_id,
        next_run_at=now - timedelta(minutes=5),
        retry_count=0,
        max_retries=2,
    )
    await _insert_task(task)

    config = _make_engine_config()
    bot = MagicMock()
    bot.send_message = AsyncMock()
    engine = FollowUpEngine(config, bot)

    await engine._send_followup(task)

    bot.send_message.assert_awaited_once()
    sent = bot.send_message.call_args[1]["text"]
    assert sent == "Test existing John", "existing appointment template should be used instead of initial"


# ─── CRITICAL 3: send_followup error recovery ────────────────────────────────


@pytest.mark.asyncio
async def test_send_followup_error_recovery(db):
    lead = await create_lead(502)
    apply_transition(lead, LeadState.FOLLOWUP_PENDING)
    await update_lead(lead)

    now = datetime.now(UTC)
    task = _make_task(lead.id, lead.channel_user_id, next_run_at=now - timedelta(minutes=5), retry_count=0)
    await _insert_task(task)

    config = _make_engine_config()
    bot = MagicMock()
    bot.send_message = AsyncMock(side_effect=Exception("Telegram API error"))
    engine = FollowUpEngine(config, bot)

    await engine._send_followup(task)

    due = await _get_due_tasks(datetime.now(UTC))
    task_after = next((t for t in due if t.id == task.id), None)
    assert task_after is not None, "task should still be due after error"
    assert task_after.status == "pending", "task status should be reset to pending after error"


# ─── CRITICAL 4: Dual acquire ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_followup_dual_acquire(db):
    lead = await create_lead(503)
    apply_transition(lead, LeadState.FOLLOWUP_PENDING)
    await update_lead(lead)

    now = datetime.now(UTC)
    task = _make_task(
        lead.id,
        lead.channel_user_id,
        next_run_at=now - timedelta(minutes=5),
        retry_count=0,
        max_retries=1,
    )
    await _insert_task(task)

    config = _make_engine_config()
    bot = MagicMock()
    bot.send_message = AsyncMock()
    engine = FollowUpEngine(config, bot)

    coros = [engine._send_followup(task), engine._send_followup(task)]
    await asyncio.gather(*coros)

    assert bot.send_message.call_count == 1, "only one send_followup should proceed"


# ─── Graceful shutdown (observable behavior) ─────────────────────────────────


@pytest.mark.asyncio
async def test_followup_engine_stop_cancels_background_task():
    config = _make_engine_config()
    bot = MagicMock()
    engine = FollowUpEngine(config, bot)

    with patch.object(engine, "_run_loop", new_callable=AsyncMock) as mock_run_loop:
        await engine.start()
        await asyncio.sleep(0)
        await engine.stop()

    mock_run_loop.assert_awaited_once()


@pytest.mark.asyncio
async def test_followup_engine_start_then_stop_no_crash():
    config = _make_engine_config()
    bot = MagicMock()
    engine = FollowUpEngine(config, bot)

    await engine.start()
    await engine.stop()

    # повторный stop не должен падать
    await engine.stop()


@pytest.mark.asyncio
async def test_followup_engine_restart_after_stop():
    config = _make_engine_config()
    bot = MagicMock()
    engine = FollowUpEngine(config, bot)

    await engine.start()
    await engine.stop()

    with patch.object(engine, "_run_loop", new_callable=AsyncMock) as mock_run_loop:
        await engine.start()
        await asyncio.sleep(0.01)
        assert mock_run_loop.called, "_run_loop should be called after restart"


@pytest.mark.asyncio
async def test_followup_engine_stop_no_task_not_crash():
    config = _make_engine_config()
    bot = MagicMock()
    engine = FollowUpEngine(config, bot)

    await engine.stop()
    # не должно быть ошибки — простая проверка отсутствия исключения
