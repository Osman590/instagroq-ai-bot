import os
from datetime import datetime

import requests
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ---------- ENV ----------
BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()
MINIAPP_URL = (os.getenv("MINIAPP_URL") or "").strip()

# ✅ В Railway у тебя переменная LOG_GROUP_ID (супергруппа -100...)
LOG_GROUP_ID = int((os.getenv("LOG_GROUP_ID") or "0").strip())

# ✅ username бота (без @). Можно НЕ задавать, если не нужно для групп.
BOT_USERNAME = (os.getenv("BOT_USERNAME") or "InstaGroqai_bot").strip()


def is_valid_https_url(url: str) -> bool:
    return url.startswith("https://") and len(url) > len("https://")


def main_menu() -> InlineKeyboardMarkup:
    keyboard = []

    if is_valid_https_url(MINIAPP_URL):
        keyboard.append([
            InlineKeyboardButton(
                "🚀 Открыть Mini App",
                web_app=WebAppInfo(url=MINIAPP_URL),
            )
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(
                "🚀 Mini App (URL не настроен)",
                callback_data="miniapp_not_set",
            )
        ])

    keyboard.append([InlineKeyboardButton("⭐ Купить пакет", callback_data="buy_pack")])
    keyboard.append([
        InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
        InlineKeyboardButton("❓ Помощь", callback_data="help"),
    ])

    return InlineKeyboardMarkup(keyboard)


def send_log_http(text: str):
    """
    Надёжная отправка в группу через Telegram HTTP API.
    Пишет ошибку в Railway Logs, если что-то не так.
    """
    if not BOT_TOKEN:
        print("LOG ERROR: BOT_TOKEN empty")
        return
    if not LOG_GROUP_ID:
        print("LOG ERROR: LOG_GROUP_ID empty/0")
        return

    try:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": LOG_GROUP_ID, "text": text},
            timeout=12,
        )
        if not r.ok:
            print("LOG ERROR:", r.status_code, r.text)
    except Exception as e:
        print("LOG ERROR: requests exception:", e)


def build_start_log(update: Update) -> str:
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    username = (user.username or "—") if user else "—"
    full_name = f"{(user.first_name or '') if user else ''} {(user.last_name or '') if user else ''}".strip() or "—"

    chat_type = chat.type if chat else "—"
    chat_id = chat.id if chat else "—"
    text = (msg.text or "").strip() if msg else ""

    return (
        "🚀 /start\n"
        f"🕒 {time_str}\n"
        f"👤 {full_name} (@{username})\n"
        f"🆔 user_id: {user.id if user else '—'}\n"
        f"💬 chat_type: {chat_type}\n"
        f"🏷 chat_id: {chat_id}\n"
        f"✉️ text: {text}"
    )


# ---------- HANDLERS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1) лог в группу
    send_log_http(build_start_log(update))

    # 2) ответ пользователю
    if update.effective_message:
        await update.effective_message.reply_text(
            "🤖 InstaGroq AI\n\nВыбирай действие кнопками ниже 👇",
            reply_markup=main_menu(),
        )


# ✅ на случай групп: /start или /start@BotUserName
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


# ---------- START BOT ----------
def start_bot():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # групповой вариант
    start_pattern = rf"^/start(@{BOT_USERNAME})?(\s|$)"
    app.add_handler(MessageHandler(filters.Regex(start_pattern), start_from_text))

    app.add_handler(CallbackQueryHandler(on_button))

    print("🤖 Telegram bot started")
    app.run_polling(stop_signals=None, close_loop=False)