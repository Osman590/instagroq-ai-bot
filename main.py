import os
import threading
from flask import Flask, request, jsonify

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from groq import Groq

# ================== ENV ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
MINIAPP_URL = os.getenv("MINIAPP_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ================== GROQ ==================
client = Groq(api_key=GROQ_API_KEY)

# ================== FLASK ==================
api = Flask(__name__)

@api.get("/health")
def health():
    return "ok"

@api.post("/api/chat")
def api_chat():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"error": "empty"}), 400

    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "Ты полезный ИИ помощник."},
            {"role": "user", "content": text},
        ],
        temperature=0.7,
        max_tokens=400,
    )

    return jsonify({"reply": resp.choices[0].message.content})

def run_flask():
    api.run(host="0.0.0.0", port=8000)

# ================== TELEGRAM ==================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Открыть Mini App", web_app=WebAppInfo(url=MINIAPP_URL))],
        [InlineKeyboardButton("⭐ Купить пакет сообщений", callback_data="buy_pack")],
        [
            InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
            InlineKeyboardButton("❓ Помощь", callback_data="help"),
        ],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 InstaGroq AI\n\nВыбирай действие 👇",
        reply_markup=main_menu(),
    )

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN not set")

    # Flask — в отдельном потоке
    threading.Thread(target=run_flask, daemon=True).start()

    # Telegram — В ГЛАВНОМ ПОТОКЕ
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    app.run_polling()

if __name__ == "__main__":
    main()
