import asyncio
import logging
import signal

from src.channels.telegram.bot import create_bot
from src.followup import FollowUpEngine
from src.monitoring.heartbeat import HeartbeatWriter
from src.storage.database import close_connection, init_db

logger = logging.getLogger(__name__)


async def run_telegram(config) -> None:
    await init_db()

    heartbeat = HeartbeatWriter("telegram", config.monitoring.heartbeat_interval)
    await heartbeat.start()

    try:
        bot = create_bot(config)
    except Exception as e:
        logger.error("Failed to create bot: %s", e, exc_info=True)
        return

    engine = FollowUpEngine(config, bot.bot)
    followup_engine: FollowUpEngine | None = engine
    bot.bot_data["followup_engine"] = followup_engine

    try:
        await engine.start()
    except Exception as e:
        logger.error("Failed to start followup engine: %s", e, exc_info=True)
        followup_engine = None

    assert bot.updater is not None
    updater = bot.updater

    try:
        await bot.initialize()
        await bot.start()
        logger.info("Bot started (client: %s)", config.client_name)
        await updater.start_polling()

        shutdown_event = asyncio.Event()
        loop = asyncio.get_running_loop()

        def _on_shutdown() -> None:
            logger.info("Shutdown signal received")
            shutdown_event.set()

        loop.add_signal_handler(signal.SIGINT, _on_shutdown)
        loop.add_signal_handler(signal.SIGTERM, _on_shutdown)

        await shutdown_event.wait()
    finally:
        logger.info("Shutting down telegram...")
        await heartbeat.stop()
        if followup_engine:
            await followup_engine.stop()
        await updater.stop()
        await bot.stop()
        await bot.shutdown()
        await close_connection()


if __name__ == "__main__":
    from src.bootstrap import bootstrap

    cfg = bootstrap()["config"]

    if not cfg.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN is not set. Create .env from .env.example")
    else:
        asyncio.run(run_telegram(cfg))