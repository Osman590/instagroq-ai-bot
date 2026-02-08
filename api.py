import os
from datetime import datetime
from typing import Any, Dict

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

from groq_client import ask_groq

# ---------- FLASK API ----------
api = Flask(__name__)
CORS(api)

# ✅ Куда слать логи (группа)
TARGET_GROUP_ID = int(os.getenv("TARGET_GROUP_ID") or "-4697406654")

# ✅ Токен нужен, чтобы API мог отправлять сообщения в Telegram
BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()


def send_log_to_group(text: str):
    if not BOT_TOKEN or not TARGET_GROUP_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": TARGET_GROUP_ID, "text": text},
            timeout=8,
        )
    except Exception:
        pass


@api.get("/")
def root():
    return "ok"


@api.get("/health")
def health():
    return "ok"


@api.post("/api/chat")
def api_chat():
    """
    Mini App → POST /api/chat
    Body:
    {
      "text": "...",
      "lang": "ru",
      "style": "steps",
      "persona": "friendly",
      "tg_user_id": 123,          (опционально)
      "tg_username": "name",      (опционально)
      "tg_first_name": "A"        (опционально)
    }
    """
    data: Dict[str, Any] = request.get_json(silent=True) or {}

    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "empty"}), 400

    lang = data.get("lang") or "ru"
    style = data.get("style") or "steps"
    persona = data.get("persona") or "friendly"

    # опционально — если миниапп передаст
    tg_user_id = data.get("tg_user_id") or "—"
    tg_username = data.get("tg_username") or "—"
    tg_first_name = data.get("tg_first_name") or "—"

    try:
        reply = ask_groq(text, lang=lang, style=style, persona=persona)
    except Exception as e:
        send_log_to_group(f"❌ Ошибка /api/chat: {e}")
        return jsonify({"error": str(e)}), 500

    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_text = (
        "🧩 Mini App чат\n"
        f"🕒 {time_str}\n"
        f"👤 {tg_first_name} (@{tg_username})\n"
        f"🆔 user_id: {tg_user_id}\n"
        f"💬 USER: {text}\n"
        f"🤖 AI: {reply}"
    )
    send_log_to_group(log_text)

    return jsonify({"reply": reply})