from typing import Any, Dict
from datetime import datetime
import os
import requests

from flask import Flask, request, jsonify
from flask_cors import CORS

from groq_client import ask_groq

# ---------- FLASK API ----------
api = Flask(__name__)
CORS(api)

# ✅ токен бота и группа для логов
BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()
TARGET_GROUP_ID = int(os.getenv("TARGET_GROUP_ID") or "-4697406654")


def send_to_group(text: str) -> None:
    if not BOT_TOKEN or not TARGET_GROUP_ID:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TARGET_GROUP_ID,
        "text": text,
        "disable_web_page_preview": True,
    }
    # если не смогло отправить — просто молча не ломаем чат
    try:
        requests.post(url, json=payload, timeout=8)
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
      "persona": "friendly"
    }
    """
    data: Dict[str, Any] = request.get_json(silent=True) or {}

    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "empty"}), 400

    lang = data.get("lang") or "ru"
    style = data.get("style") or "steps"
    persona = data.get("persona") or "friendly"

    # ✅ логируем входящий текст в группу
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    send_to_group(
        "📩 MiniApp: новый запрос\n"
        f"🕒 {ts}\n"
        f"🌐 lang={lang} | style={style} | persona={persona}\n"
        f"💬 {text}"
    )

    try:
        reply = ask_groq(text, lang=lang, style=style, persona=persona)
    except Exception as e:
        send_to_group(f"❌ MiniApp: ошибка\n🕒 {ts}\n{str(e)}")
        return jsonify({"error": str(e)}), 500

    # ✅ логируем ответ ИИ в группу
    send_to_group(
        "🤖 MiniApp: ответ ИИ\n"
        f"🕒 {ts}\n"
        f"📝 {reply}"
    )

    return jsonify({"reply": reply})