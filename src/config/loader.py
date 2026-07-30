import os
from dataclasses import dataclass


@dataclass
class Config:
    telegram_bot_token: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    client_name: str = "demo_dental"
    debug: bool = False


def load_config() -> Config:
    return Config(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        client_name=os.getenv("DENTALFLOW_CLIENT", "demo_dental"),
        debug=os.getenv("DEBUG", "").lower() in ("1", "true", "yes"),
    )