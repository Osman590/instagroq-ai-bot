# bot_handlers.py
import os

from telegram import Update
from telegram.ext import ContextTypes

from bot_menu import main_menu
from bot_logging import send_log_http, build_start_log


# ---------- ENV ----------
MINIAPP_URL = (os.getenv("MINIAPP_URL") or "").strip()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1) лог в группу
    send_log_http(build_start_log(update))

    # 2) ответ пользователю
    if update.effective_message:
        await update.effective_message.reply_text(
            "🤖 InstaGroq AI\n\nВыбирай действие кнопками ниже 👇",
            reply_markup=main_menu(MINIAPP_URL),
        )


# на случай групп: /start или /start@BotUserName
async def start_from_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "miniapp_not_set":
        await query.message.reply_text(
            "⚠️ MINIAPP_URL не настроен.\n\n"
            "Добавь в Railway → Variables:\n"
            "MINIAPP_URL = https://<твой-github-pages>"
        )
        return

    if data == "buy_pack":
        await query.message.reply_text(
            "⭐ Пакеты сообщений (пример):\n"
            "• 100 сообщений — 99₽\n"
            "• 500 сообщений — 399₽\n"
            "• 2000 сообщений — 999₽\n\n"
            "Оплату подключим позже."
        )
        return

    if data == "settings":
        await query.message.reply_text("⚙️ Настройки скоро появятся.")
        return

    if data == "help":
        await query.message.reply_text("❓ Нажми «Открыть Mini App» и пиши в чат внутри Mini App.")
        return