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
        await self._send(service, "DOWN")

    async def send_recovered(self, service: str) -> None:
        await self._send(service, "RECOVERED")

    async def _send(self, service: str, status: str) -> None:
        chat_id = self._config.monitoring.alerts_chat_id
        if not chat_id:
            logger.info("No alerts_chat_id configured — skipping alert for %s", service)
            return
        text = f"🚨 *{status}*: {service}"
        try:
            await self._bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
            logger.info("Alert sent: %s %s", status, service)
        except Exception as e:  # noqa: BLE001
            logger.error("Failed to send %s alert for %s: %s", status, service, e)
