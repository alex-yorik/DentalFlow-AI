from telegram import Update
from telegram.ext import ContextTypes


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome to DentalFlow AI! I'm your dental clinic assistant. "
        "How can I help you today?"
    )