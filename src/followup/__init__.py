import asyncio
import logging
import uuid
from datetime import UTC, datetime, timedelta, timezone

import aiosqlite
from telegram import Bot

from src.config.loader import AppConfig, FollowUpConfig
from src.followup.models import FollowUpTask
from src.integrations.notifications import notify_staff_followup_complete
from src.leads.models import Lead, LeadState
from src.leads.repository import get_lead_by_chat_id, update_lead
from src.leads.state_machine import apply_transition
from src.storage import database
from src.storage.appointment_repository import find_existing_appointment
from src.storage.database import StorageError

logger = logging.getLogger(__name__)

_RESCHEDULE_DELAY = timedelta(minutes=1)


async def _insert_task(task: FollowUpTask) -> None:
    try:
        conn = await database.get_connection()
    except StorageError:
        raise

    try:
        await conn.execute(
            """INSERT INTO followup_tasks
               (id, lead_id, chat_id, retry_count, max_retries, next_run_at, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                task.id, task.lead_id, task.chat_id,
                task.retry_count, task.max_retries,
                task.next_run_at.isoformat(), task.status,
                task.created_at.isoformat(), task.updated_at.isoformat(),
            ),
        )
        await conn.commit()
    except (aiosqlite.Error, StorageError) as e:
        logger.error("StorageError: _insert_task(id=%s, lead_id=%s) failed: %s", task.id, task.lead_id, e)
        raise StorageError(f"_insert_task failed for task {task.id}: {e}") from e
    finally:
        await conn.close()


async def _update_task(task: FollowUpTask) -> None:
    task.updated_at = datetime.now(UTC)
    try:
        conn = await database.get_connection()
    except StorageError:
        raise

    try:
        await conn.execute(
            """UPDATE followup_tasks SET
               retry_count=?, next_run_at=?, status=?, updated_at=?
               WHERE id=?""",
            (
                task.retry_count, task.next_run_at.isoformat(),
                task.status, task.updated_at.isoformat(), task.id,
            ),
        )
        await conn.commit()
    except (aiosqlite.Error, StorageError) as e:
        logger.error("StorageError: _update_task(id=%s, lead_id=%s) failed: %s", task.id, task.lead_id, e)
        raise StorageError(f"_update_task failed for task {task.id}: {e}") from e
    finally:
        await conn.close()


async def _update_task_status(task_id: str, status: str) -> None:
    now = datetime.now(UTC)
    try:
        conn = await database.get_connection()
    except StorageError:
        return

    try:
        await conn.execute(
            "UPDATE followup_tasks SET status=?, updated_at=? WHERE id=?",
            (status, now.isoformat(), task_id),
        )
        await conn.commit()
    except (aiosqlite.Error, StorageError) as e:
        logger.error("StorageError: _update_task_status(id=%s) failed: %s", task_id, e)
    finally:
        await conn.close()


async def _cancel_tasks_by_lead(lead_id: str) -> None:
    now = datetime.now(UTC)
    try:
        conn = await database.get_connection()
    except StorageError:
        return

    try:
        await conn.execute(
            "UPDATE followup_tasks SET status='cancelled', updated_at=? WHERE lead_id=? AND status='pending'",
            (now.isoformat(), lead_id),
        )
        await conn.commit()
    except (aiosqlite.Error, StorageError) as e:
        logger.error("StorageError: _cancel_tasks_by_lead(lead_id=%s) failed: %s", lead_id, e)
    finally:
        await conn.close()


async def _acquire_task(task_id: str) -> bool:
    now = datetime.now(UTC)
    try:
        conn = await database.get_connection()
    except StorageError:
        return False

    try:
        cursor = await conn.execute(
            "UPDATE followup_tasks SET status='running', updated_at=? WHERE id=? AND status='pending'",
            (now.isoformat(), task_id),
        )
        await conn.commit()
        return cursor.rowcount > 0
    except (aiosqlite.Error, StorageError) as e:
        logger.error("StorageError: _acquire_task(id=%s) failed: %s", task_id, e)
        return False
    finally:
        await conn.close()


async def _get_due_tasks(now: datetime) -> list[FollowUpTask]:
    try:
        conn = await database.get_connection()
    except StorageError:
        return []

    try:
        cursor = await conn.execute(
            "SELECT * FROM followup_tasks WHERE status='pending' AND next_run_at <= ?",
            (now.isoformat(),),
        )
        rows = await cursor.fetchall()
        return [_row_to_task(r) for r in rows]
    except (aiosqlite.Error, StorageError) as e:
        logger.error("StorageError: _get_due_tasks failed: %s", e)
        return []
    finally:
        await conn.close()


async def _get_pending_tasks() -> list[FollowUpTask]:
    try:
        conn = await database.get_connection()
    except StorageError:
        return []

    try:
        cursor = await conn.execute(
            "SELECT * FROM followup_tasks WHERE status='pending'",
        )
        rows = await cursor.fetchall()
        return [_row_to_task(r) for r in rows]
    except (aiosqlite.Error, StorageError) as e:
        logger.error("StorageError: _get_pending_tasks failed: %s", e)
        return []
    finally:
        await conn.close()


def _row_to_task(row) -> FollowUpTask:
    return FollowUpTask(
        id=row["id"],
        lead_id=row["lead_id"],
        chat_id=row["chat_id"],
        retry_count=row["retry_count"],
        max_retries=row["max_retries"],
        next_run_at=datetime.fromisoformat(row["next_run_at"]),
        status=row["status"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


class FollowUpEngine:
    def __init__(self, config: AppConfig, bot: Bot):
        self.config = config
        self.bot = bot
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("FollowUpEngine started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("FollowUpEngine stopped")

    async def schedule_followup(self, lead: Lead) -> None:
        if lead.followup_task_id:
            logger.info("Follow-up already scheduled for lead %s", lead.id)
            return

        delay = self.config.client.followup.delay_minutes
        next_run = datetime.now(UTC) + timedelta(minutes=delay)

        task = FollowUpTask(
            id=str(uuid.uuid4()),
            lead_id=lead.id,
            chat_id=lead.channel_user_id,
            max_retries=self.config.client.followup.max_retries,
            next_run_at=next_run,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        await _insert_task(task)
        lead.followup_task_id = task.id
        logger.info("Follow-up scheduled for lead %s, task %s, next run %s", lead.id, task.id, next_run.isoformat())

    async def cancel_followup(self, lead_id: str) -> None:
        await _cancel_tasks_by_lead(lead_id)
        logger.info("Follow-up cancelled for lead %s", lead_id)

    async def _run_loop(self) -> None:
        await self._reschedule_pending()
        interval = self.config.client.followup.poll_interval_seconds
        while self._running:
            try:
                await self._process_due_tasks()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("FollowUpEngine loop error: %s", e)
                await asyncio.sleep(interval)

    async def _reschedule_pending(self) -> None:
        tasks = await _get_pending_tasks()
        now = datetime.now(UTC)
        for task in tasks:
            if task.next_run_at <= now:
                task.next_run_at = now + _RESCHEDULE_DELAY
                await _update_task(task)
                logger.info("Rescheduled stale follow-up task %s for lead %s", task.id, task.lead_id)

    async def _process_due_tasks(self) -> None:
        now = datetime.now(UTC)
        tasks = await _get_due_tasks(now)
        for task in tasks:
            try:
                await self._send_followup(task)
            except Exception as e:
                logger.error("Failed to send follow-up task %s: %s", task.id, e)

    async def _send_followup(self, task: FollowUpTask) -> None:
        acquired = await _acquire_task(task.id)
        if not acquired:
            return

        lead = await get_lead_by_chat_id(task.chat_id)
        if not lead or lead.state != LeadState.FOLLOWUP_PENDING:
            await _update_task_status(task.id, "cancelled")
            return

        followup = self.config.client.followup
        appointment = await find_existing_appointment(lead.name, lead.phone)
        template = self._get_template(followup, task.retry_count, appointment is not None)
        if not template:
            await _update_task_status(task.id, "cancelled")
            return

        message = template.format(
            name=lead.name or "",
            service_interest=lead.service_interest or "",
        )

        try:
            await self.bot.send_message(chat_id=task.chat_id, text=message)
        except Exception as e:
            logger.error("Failed to send follow-up message to chat %s: %s", task.chat_id, e)
            await _update_task_status(task.id, "pending")
            return

        task.retry_count += 1
        if task.retry_count >= task.max_retries:
            apply_transition(lead, LeadState.CLOSED)
            await update_lead(lead)
            await _update_task_status(task.id, "completed")
            await notify_staff_followup_complete(self.config, lead, self.bot)
            logger.info("Follow-up completed for lead %s (max retries reached)", lead.id)
        else:
            delay = timedelta(minutes=followup.delay_minutes)
            task.next_run_at = datetime.now(UTC) + delay
            task.status = "pending"
            await _update_task(task)
            logger.info(
                "Follow-up sent for lead %s (retry %d/%d), next run %s",
                lead.id, task.retry_count, task.max_retries, task.next_run_at.isoformat(),
            )

    def _get_template(self, followup: FollowUpConfig, retry_count: int, has_appointment: bool = False) -> str | None:
        if retry_count == 0:
            return followup.templates.get("existing_appointment") if has_appointment else followup.templates.get("initial")
        elif retry_count < followup.max_retries:
            return followup.templates.get("reminder")
        return followup.templates.get("final")
