import asyncio
import logging
import os
import threading

import uvicorn

from src.bootstrap import bootstrap
from src.core.logging import uvicorn_log_config
from src.entrypoints.telegram import run_telegram
from src.entrypoints.web import _build_web_app

"""DEV-ONLY entry point — do NOT use in production.

Production runs separate entrypoints via docker-compose:
  src.entrypoints.telegram / web / followup.
Running uvicorn in a thread (+) telegram via asyncio.run in one
process mixes two event loops (event-loop race). Use entrypoints.
"""

logger = logging.getLogger(__name__)


async def main() -> None:
    config = bootstrap()["config"]

    logger.warning("src.main is DEV-ONLY; production uses src.entrypoints.* via docker-compose")

    if not config.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN is not set. Create .env from .env.example")
        return

    web_app = _build_web_app(config)
    web_thread = threading.Thread(
        target=uvicorn.run,
        args=(web_app,),
        kwargs={
            "host": config.web_host,
            "port": config.web_port,
            "log_level": config.log_level.lower(),
            "log_config": uvicorn_log_config(config.log_level, os.getenv("LOG_FORMAT", "json")),
        },
        daemon=True,
    )
    web_thread.start()
    logger.info("Web channel started on http://%s:%s", config.web_host, config.web_port)

    await run_telegram(config)


if __name__ == "__main__":
    asyncio.run(main())