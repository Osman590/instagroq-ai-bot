import os
import json
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import Application, CommandHandler, ContextTypes

from flask import Flask, request, jsonify
from threading import Thread

from groq import Groq

# ---------- ENV ----------
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MINIAPP_URL = "https://osman590.github.io/instagroq-ai-bot/"

# ---------- GROQ ----------
groq = Groq(api_key=GROQ_API_KEY)

# ---------- TELEGRAM BOT ----------
def main_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "🚀 Открыть Mini App",
                web_app=WebAppInfo(url=MINIAPP_URL),
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 InstaGroq AI\n\nОткрой Mini App 👇",
        reply_markup=main_menu(),
    )

def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

# ---------- API SERVER ----------
api = Flask(__name__)

@api.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "empty"}), 400

    resp = groq.chat.completions.create(
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

# ---------- MAIN ----------
if __name__ == "__main__":
    Thread(target=run_bot).start()
    api.run(host="0.0.0.0", port=8000)
