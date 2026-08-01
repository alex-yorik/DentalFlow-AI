import asyncio
import logging
import signal
import threading

import uvicorn

from src.config.loader import load_config
from src.channels.telegram.bot import create_bot
from src.channels.web.adapter import router as web_router
from src.followup import FollowUpEngine
from src.llm.client import LLMClient
from src.storage.database import close_connection, init_db

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


def _build_web_app(config):
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(title="DentalFlow AI Web Channel")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(web_router)
    app.state.config = config
    app.state.llm_client = LLMClient(
        api_key=config.openai_api_key,
        model=config.openai_model,
    )
    return app


async def main() -> None:
    config = load_config()

    if not config.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN is not set. Create .env from .env.example")
        return

    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error("Failed to initialize database: %s", e, exc_info=True)
        return

    web_app = _build_web_app(config)
    web_thread = threading.Thread(
        target=uvicorn.run,
        args=(web_app,),
        kwargs={"host": config.web_host, "port": config.web_port, "log_level": "info"},
        daemon=True,
    )
    web_thread.start()
    logger.info("Web channel started on http://%s:%s", config.web_host, config.web_port)

    try:
        bot = create_bot(config)
    except Exception as e:
        logger.error("Failed to create bot: %s", e, exc_info=True)
        return

    followup_engine = FollowUpEngine(config, bot.bot)
    bot.bot_data["followup_engine"] = followup_engine

    try:
        await followup_engine.start()
    except Exception as e:
        logger.error("Failed to start followup engine: %s", e, exc_info=True)
        followup_engine = None

    try:
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
    finally:
        logger.info("Shutting down...")
        if followup_engine:
            await followup_engine.stop()
        await bot.updater.stop()
        await bot.stop()
        await bot.shutdown()
        await close_connection()


if __name__ == "__main__":
    asyncio.run(main())