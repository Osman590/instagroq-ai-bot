import os
from threading import Thread

from flask import Flask, request, jsonify
from groq import Groq

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

# -------- ENV --------
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

# ссылка на твой Mini App (GitHub Pages)
MINIAPP_URL = "https://osman590.github.io/instagroq-ai-bot/"

# -------- GROQ --------
client = Groq(api_key=GROQ_API_KEY)

# -------- FLASK API --------
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
    answer = resp.choices[0].message.content
    return jsonify({"reply": answer})

# -------- TELEGRAM BOT --------
def main_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🚀 Открыть Mini App", web_app=WebAppInfo(url=MINIAPP_URL))],
        [InlineKeyboardButton("⭐ Купить пакет сообщений", callback_data="buy_pack")],
        [
            InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
            InlineKeyboardButton("❓ Помощь", callback_data="help"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 InstaGroq AI\n\nВыбирай действие кнопками ниже 👇",
        reply_markup=main_menu(),
    )

def run_bot():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set")

    Thread(target=run_bot, daemon=True).start()
    api.run(host="0.0.0.0", port=8000)