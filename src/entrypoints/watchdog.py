import asyncio
import logging
import signal

from telegram import Bot

from src.monitoring.alerter import Alerter
from src.monitoring.watchdog import Watchdog
from src.storage.database import close_connection, init_db

logger = logging.getLogger(__name__)


async def run_watchdog(config) -> None:
    await init_db()

    bot = Bot(token=config.telegram_bot_token)
    watchdog = Watchdog(config)
    alerter = Alerter(config, bot)

    shutdown_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _on_shutdown() -> None:
        logger.info("Shutdown signal received")
        shutdown_event.set()

    loop.add_signal_handler(signal.SIGINT, _on_shutdown)
    loop.add_signal_handler(signal.SIGTERM, _on_shutdown)

    # Workers share the same SQLite file; give them a moment to report
    # their first heartbeat before the initial probe.
    await asyncio.sleep(config.monitoring.heartbeat_interval)

    while not shutdown_event.is_set():
        try:
            events = await watchdog.tick()
            for event in events:
                if event.is_down:
                    await alerter.send_down(event.service)
                else:
                    await alerter.send_recovered(event.service)
            if events:
                logger.info("Watchdog events: %s", [e.kind + ":" + e.service for e in events])
        except Exception as e:  # noqa: BLE001
            logger.error("Watchdog tick failed: %s", e)
        try:
            await asyncio.wait_for(shutdown_event.wait(), timeout=config.monitoring.watchdog_interval)
        except TimeoutError:
            pass

    await close_connection()


if __name__ == "__main__":
    from src.bootstrap import bootstrap

    cfg = bootstrap()["config"]

    if not cfg.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN is not set. Create .env from .env.example")
    else:
        asyncio.run(run_watchdog(cfg))
