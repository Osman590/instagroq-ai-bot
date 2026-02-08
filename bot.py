# bot.py
import os

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from bot_handlers import start, start_from_text, on_button
from bot_logging import init_env

# ---------- ENV ----------
BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()
BOT_USERNAME = (os.getenv("BOT_USERNAME") or "InstaGroqai_bot").strip()


def start_bot():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    # инициализируем env/логирование (ничего не меняет, просто готовит переменные)
    init_env()

    app = Application.builder().token(BOT_TOKEN).build()

    # /start
    app.add_handler(CommandHandler("start", start))

    # групповой вариант: /start или /start@BotUserName
    start_pattern = rf"^/start(@{BOT_USERNAME})?(\s|$)"
    app.add_handler(MessageHandler(filters.Regex(start_pattern), start_from_text))

    # кнопки
    app.add_handler(CallbackQueryHandler(on_button))

    print("🤖 Telegram bot started")
    app.run_polling(stop_signals=None, close_loop=False)