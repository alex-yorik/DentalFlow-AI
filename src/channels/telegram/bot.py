from telegram.ext import Application, CommandHandler, MessageHandler, filters

from src.config.loader import AppConfig
from src.channels.telegram.handlers import start_command, handle_message
from src.llm.client import LLMClient


def create_bot(config: AppConfig) -> Application:
    application = Application.builder().token(config.telegram_bot_token).build()
    application.bot_data["config"] = config
    application.bot_data["llm_client"] = LLMClient(
        api_key=config.openai_api_key,
        model=config.openai_model,
    )
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return application