import logging
import os

from src.config.loader import load_config, validate_required_env
from src.core.logging import setup_logging
from src.llm.client import LLMClient

logger = logging.getLogger(__name__)


def bootstrap() -> dict:
    validate_required_env()
    config = load_config()
    setup_logging(config.log_level, os.getenv("LOG_FORMAT", "json"))
    llm_client = LLMClient(
        api_key=config.openai_api_key,
        model=config.openai_model,
        base_url=config.base_url,
    )
    logger.info("Config loaded: client=%s", config.client_name)
    return {"config": config, "llm_client": llm_client}
