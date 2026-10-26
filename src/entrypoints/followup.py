import asyncio
import logging
import signal

from telegram.ext import Application

from src.followup import FollowUpEngine
from src.monitoring.heartbeat import HeartbeatWriter
from src.storage.database import close_connection, init_db

logger = logging.getLogger(__name__)


async def run_followup(config) -> None:
    await init_db()

    heartbeat = HeartbeatWriter("followup", config.monitoring.heartbeat_interval)
    await heartbeat.start()

    app = Application.builder().token(config.telegram_bot_token).build()
    followup_engine = FollowUpEngine(config, app.bot)

    try:
        await followup_engine.start()
        logger.info("FollowUp engine started")

        shutdown_event = asyncio.Event()
        loop = asyncio.get_running_loop()

        def _on_shutdown() -> None:
            logger.info("Shutdown signal received")
            shutdown_event.set()

        loop.add_signal_handler(signal.SIGINT, _on_shutdown)
        loop.add_signal_handler(signal.SIGTERM, _on_shutdown)

        await shutdown_event.wait()
    finally:
        logger.info("Shutting down followup...")
        await heartbeat.stop()
        await followup_engine.stop()
        await close_connection()


if __name__ == "__main__":
    from src.bootstrap import bootstrap

    cfg = bootstrap()["config"]

    if not cfg.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN is not set. Create .env from .env.example")
    else:
        asyncio.run(run_followup(cfg))
