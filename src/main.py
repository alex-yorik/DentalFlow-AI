import asyncio
import logging
import signal

from src.config.loader import load_config
from src.channels.telegram.bot import create_bot
from src.followup import FollowUpEngine
from src.storage.database import init_db

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


async def main() -> None:
    config = load_config()

    if not config.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN is not set. Create .env from .env.example")
        return

    await init_db()
    logger.info("Database initialized")

    bot = create_bot(config)
    followup_engine = FollowUpEngine(config, bot.bot)
    bot.bot_data["followup_engine"] = followup_engine
    await followup_engine.start()

    await bot.initialize()
    await bot.start()
    logger.info("Bot started (client: %s)", config.client_name)
    await bot.updater.start_polling()

    shutdown_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _on_shutdown() -> None:
        logger.info("Shutdown signal received")
        shutdown_event.set()

    loop.add_signal_handler(signal.SIGINT, _on_shutdown)
    loop.add_signal_handler(signal.SIGTERM, _on_shutdown)

    await shutdown_event.wait()

    logger.info("Shutting down...")
    await followup_engine.stop()
    await bot.updater.stop()
    await bot.stop()
    await bot.shutdown()


if __name__ == "__main__":
    asyncio.run(main())