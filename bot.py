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

# ✅ Лог-чат (Railway Variable: LOG_GROUP_ID)
LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID") or "0")

# ✅ ВАЖНО: username бота (как в @InstaGroqai_bot, без @)
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


async def log_to_group(context: ContextTypes.DEFAULT_TYPE, text: str):
    if not LOG_GROUP_ID:
        return
    try:
        await context.bot.send_message(chat_id=LOG_GROUP_ID, text=text)
    except Exception:
        pass


def build_start_log(update: Update) -> str:
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    username = (user.username or "—") if user else "—"
    full_name = f"{(user.first_name or '') if user else ''} {(user.last_name or '') if user else ''}".strip() or "—"

    chat_type = chat.type if chat else "—"
    chat_id = chat.id if chat else "—"

    return (
        "🚀 /start (group/private)\n"
        f"🕒 {time_str}\n"
        f"👤 {full_name} (@{username})\n"
        f"🆔 user_id: {user.id if user else '—'}\n"
        f"💬 chat_type: {chat_type}\n"
        f"🏷 chat_id: {chat_id}"
    )


# ---------- HANDLERS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # отвечаем
    if update.effective_message:
        await update.effective_message.reply_text(
            "🤖 InstaGroq AI\n\nВыбирай действие кнопками ниже 👇",
            reply_markup=main_menu(),
        )

    # логируем
    await log_to_group(context, build_start_log(update))


# ✅ ЛОВИМ /start В ГРУППЕ КАК ТЕКСТ (включая /start@BotUserName)
async def start_from_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # просто вызываем общий start
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

    # 1) стандартно: /start
    app.add_handler(CommandHandler("start", start))

    # 2) надежно для групп: ловим текст "/start" и "/start@InstaGroqai_bot"
    #    (Telegram часто требует @username именно в группе)
    start_pattern = rf"^/start(@{BOT_USERNAME})?(\s|$)"
    app.add_handler(MessageHandler(filters.Regex(start_pattern), start_from_text))

    app.add_handler(CallbackQueryHandler(on_button))

    print("🤖 Telegram bot started")
    app.run_polling(stop_signals=None, close_loop=False)