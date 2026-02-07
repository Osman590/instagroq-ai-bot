import os
import threading
from typing import Any, Dict

from flask import Flask, request, jsonify
from flask_cors import CORS  # ✅ ВОТ ЭТОГО У ТЕБЯ НЕ ХВАТАЛО

from groq import Groq

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
)

# ---------- ENV ----------
BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()
GROQ_API_KEY = (os.getenv("GROQ_API_KEY") or "").strip()
GROQ_MODEL = (os.getenv("GROQ_MODEL") or "llama-3.1-8b-instant").strip()

# ✅ ВАЖНО: это URL ФРОНТА (GitHub Pages), а не Railway домен
MINIAPP_URL = (os.getenv("MINIAPP_URL") or "").strip()

PORT = int(os.environ["PORT"])


# ---------- GROQ CLIENT ----------
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


def is_valid_https_url(url: str) -> bool:
    return url.startswith("https://") and len(url) > len("https://")


# ---------- FLASK API ----------
api = Flask(__name__)
CORS(api)  # ✅ теперь импорт есть, всё ок


@api.get("/health")
def health():
    return "ok"


@api.post("/api/chat")
def api_chat():
    """
    Mini App будет слать сюда:
    { "text": "привет" }
    Ответ:
    { "reply": "..." }
    """
    if not groq_client:
        return jsonify({"error": "GROQ_API_KEY is not set"}), 500

    data: Dict[str, Any] = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "empty"}), 400

    resp = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": "Ты полезный ИИ помощник. Отвечай кратко и по делу."},
            {"role": "user", "content": text},
        ],
        temperature=0.7,
        max_tokens=400,
    )

    answer = resp.choices[0].message.content or ""
    return jsonify({"reply": answer})


def run_flask():
    # без reloader, иначе будет второй процесс и всё ломается
    api.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)


# ---------- TELEGRAM BOT ----------
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
            InlineKeyboardButton("🚀 Mini App (URL не настроен)", callback_data="miniapp_not_set")
        ])

    keyboard.append([InlineKeyboardButton("⭐ Купить пакет сообщений", callback_data="buy_pack")])
    keyboard.append([
        InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
        InlineKeyboardButton("❓ Помощь", callback_data="help"),
    ])

    return InlineKeyboardMarkup(keyboard)


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
            "⚠️ MINIAPP_URL не настроен.\n"
            "В Railway → Variables добавь:\n"
            "MINIAPP_URL = https://osman590.github.io/instagroq-ai-bot/"
        )
        return

    if data == "buy_pack":
        await query.message.reply_text(
            "⭐ Пакеты сообщений (пример):\n"
            "• 100 сообщений — 99₽\n"
            "• 500 сообщений — 399₽\n"
            "• 2000 сообщений — 999₽\n\n"
            "Потом подключим оплату Telegram."
        )
        return

    if data == "settings":
        await query.message.reply_text("⚙️ Настройки — добавим позже (стиль ИИ, очистка чата и т.д.).")
        return

    if data == "help":
        await query.message.reply_text("❓ Помощь: нажми «Открыть Mini App» и пиши в чат внутри Mini App.")
        return


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    if not GROQ_API_KEY:
        print("WARNING: GROQ_API_KEY is not set (Mini App /api/chat will fail)")

    # ✅ Flask в отдельном потоке (так Railway увидит порт)
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()

    # ✅ Telegram в главном потоке
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_button))

    # ✅ stop_signals=None — чтобы не ловить ошибки сигналов в Railway
    app.run_polling(stop_signals=None, close_loop=False)


if __name__ == "__main__":
    main()