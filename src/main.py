import asyncio
import logging

from src.config.loader import load_config
from src.channels.telegram.bot import create_bot

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

    bot = create_bot(config)
    await bot.initialize()
    await bot.start()
    logger.info("DentalFlow AI started (bot: %s)", config.client_name)
    await bot.updater.start_polling()
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())