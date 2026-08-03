import asyncio
import logging
import signal
from pathlib import Path

from telegram import Bot

from src.config.loader import AppConfig
from src.monitoring.alerter import Alerter
from src.storage.backup import create_backup, rotate
from src.storage.database import DB_PATH

logger = logging.getLogger(__name__)

BACKUPS_DIR = Path("data/backups")


async def run_backup(config: AppConfig) -> None:
    bot = Bot(token=config.telegram_bot_token)
    alerter = Alerter(config, bot)

    shutdown_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, shutdown_event.set)
    loop.add_signal_handler(signal.SIGTERM, shutdown_event.set)

    interval = config.backup.backup_interval_hours * 3600

    while not shutdown_event.is_set():
        try:
            await asyncio.to_thread(create_backup, DB_PATH, BACKUPS_DIR)
            await asyncio.to_thread(rotate, BACKUPS_DIR, config.backup.retention_days)
            logger.info("Backup cycle completed")
        except Exception as e:  # noqa: BLE001
            logger.error("Backup failed: %s", e)
            await alerter.send_backup_failure(str(e))

        try:
            await asyncio.wait_for(shutdown_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            pass


if __name__ == "__main__":
    from src.bootstrap import bootstrap

    cfg = bootstrap()["config"]
    asyncio.run(run_backup(cfg))
