"""Send monitoring alerts (down/recovered) to a Telegram chat."""

import logging

from telegram import Bot

from src.config.loader import AppConfig

logger = logging.getLogger(__name__)


class Alerter:
    def __init__(self, config: AppConfig, bot: Bot) -> None:
        self._config = config
        self._bot = bot

    async def send_down(self, service: str) -> None:
        await self._send("DOWN", service)

    async def send_recovered(self, service: str) -> None:
        await self._send("RECOVERED", service)

    async def send_backup_failure(self, detail: str) -> None:
        await self._send("BACKUP_FAILED", detail)

    async def _send(self, status: str, subject: str) -> None:
        chat_id = self._config.monitoring.alerts_chat_id
        if not chat_id:
            logger.info("No alerts_chat_id configured — skipping alert for %s", subject)
            return
        text = f"🚨 *{status}*: {subject}"
        try:
            await self._bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
            logger.info("Alert sent: %s %s", status, subject)
        except Exception as e:  # noqa: BLE001 # alert delivery failure must not propagate
            logger.error("Failed to send %s alert for %s: %s", status, subject, e)
