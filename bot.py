import os

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

from groq_client import ask_groq  # ✅ ИИ


# ---------- ENV ----------
BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()
MINIAPP_URL = (os.getenv("MINIAPP_URL") or "").strip()


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


# ---------- HANDLERS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 InstaGroq AI\n\nВыбирай действие кнопками ниже 👇",
        reply_markup=main_menu(),
    )


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


# ---------- GROUP / DM CHAT ----------
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    text = msg.text.strip()

    # ❌ игнорируем команды
    if text.startswith("/"):
        return

    # 🧠 запрос к ИИ
    try:
        reply = ask_groq(
            text,
            lang="ru",
            style="steps",
            persona="friendly",
        )
    except Exception:
        await msg.reply_text("⚠️ Ошибка ИИ")
        return

    await msg.reply_text(reply)


# ---------- START BOT ----------
def start_bot():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_button))

    # ✅ обычные сообщения (группа + личка)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    print("🤖 Telegram bot started")
    app.run_polling(stop_signals=None, close_loop=False)