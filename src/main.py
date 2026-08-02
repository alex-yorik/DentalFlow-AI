import asyncio
import logging
import threading

import uvicorn

from src.bootstrap import bootstrap
from src.entrypoints.telegram import run_telegram
from src.entrypoints.web import _build_web_app

logger = logging.getLogger(__name__)


async def main() -> None:
    config = bootstrap()["config"]

    if not config.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN is not set. Create .env from .env.example")
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

    await run_telegram(config)


if __name__ == "__main__":
    asyncio.run(main())