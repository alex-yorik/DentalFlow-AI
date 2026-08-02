import logging

from src.config.loader import load_config
from src.llm.client import LLMClient

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


def bootstrap() -> dict:
    config = load_config()
    llm_client = LLMClient(
        api_key=config.openai_api_key,
        model=config.openai_model,
    )
    logger.info("Config loaded: client=%s", config.client_name)
    return {"config": config, "llm_client": llm_client}