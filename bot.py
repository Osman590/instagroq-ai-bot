import os
from datetime import datetime

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

# ✅ Лог-чат (как у тебя в Railway: LOG_GROUP_ID)
LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID") or "0")


def is_valid_https_url(url: str) -> bool:
    return url.startswith("https://") and len(url) > len("https://")


# ---------- KEYBOARDS ----------
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

    keyboard.append([
        InlineKeyboardButton("⭐ Купить пакет", callback_data="buy_pack"),
    ])

    keyboard.append([
        InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
        InlineKeyboardButton("❓ Помощь", callback_data="help"),
    ])

    return InlineKeyboardMarkup(keyboard)


# ---------- LOG HELPERS ----------
async def log_to_group(context: ContextTypes.DEFAULT_TYPE, text: str):
    if not LOG_GROUP_ID:
        return
    try:
        await context.bot.send_message(chat_id=LOG_GROUP_ID, text=text)
    except Exception:
        # чтобы бот не падал из-за логов
        pass


# ---------- HANDLERS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ответ пользователю
    await update.message.reply_text(
        "🤖 InstaGroq AI\n\nВыбирай действие кнопками ниже 👇",
        reply_markup=main_menu(),
    )

    # ✅ лог в группу
    msg = update.message
    user = msg.from_user
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    username = user.username or "—"
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "—"

    chat_type = msg.chat.type
    chat_id = msg.chat.id

    log_text = (
        "🚀 /start\n"
        f"🕒 {time_str}\n"
        f"👤 {full_name} (@{username})\n"
        f"🆔 user_id: {user.id}\n"
        f"💬 chat_type: {chat_type}\n"
        f"🏷 chat_id: {chat_id}"
    )
    await log_to_group(context, log_text)


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
        await query.message.reply_text(
            "⚙️ Настройки скоро появятся (стиль ИИ, очистка чата и т.д.)."
        )
        return

    if data == "help":
        await query.message.reply_text(
            "❓ Нажми «Открыть Mini App» и пиши в чат внутри Mini App."
        )
        return


# (опционально) лог обычных сообщений, если нужно
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    user = msg.from_user
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    username = user.username or "—"
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "—"

    log_text = (
        "💬 Сообщение в боте\n"
        f"🕒 {time_str}\n"
        f"👤 {full_name} (@{username})\n"
        f"🆔 user_id: {user.id}\n"
        f"{msg.text}"
    )
    await log_to_group(context, log_text)


# ---------- START BOT ----------
def start_bot():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    print("🤖 Telegram bot started")
    app.run_polling(stop_signals=None, close_loop=False)