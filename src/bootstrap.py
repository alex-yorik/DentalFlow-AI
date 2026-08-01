import logging

from src.config.loader import load_config

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


def bootstrap() -> dict:
    config = load_config()
    logger.info("Config loaded: client=%s", config.client_name)
    return {"config": config}