from telegram.ext import Application, CommandHandler

from src.config.loader import Config
from src.channels.telegram.handlers import start_command


def create_bot(config: Config) -> Application:
    application = Application.builder().token(config.telegram_bot_token).build()
    application.add_handler(CommandHandler("start", start_command))
    return application