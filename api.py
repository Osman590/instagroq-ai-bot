import os
from datetime import datetime
from typing import Any, Dict, Tuple

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


def send_log_to_group(text: str) -> Tuple[bool, str]:
    """
    Возвращает:
      (ok: bool, info: str)
    """
    if not BOT_TOKEN:
        return False, "BOT_TOKEN is empty"
    if not TARGET_GROUP_ID:
        return False, "TARGET_GROUP_ID is empty"

    try:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": TARGET_GROUP_ID, "text": text},
            timeout=12,
        )
        # Вернём ответ Telegram (очень важно для диагностики)
        return r.ok, r.text
    except Exception as e:
        return False, f"requests error: {e}"


@api.get("/")
def root():
    return "ok"


@api.get("/health")
def health():
    return "ok"


# ✅ ТЕСТ: проверяем, может ли Railway отправлять в группу
@api.get("/api/test-log")
def test_log():
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ok, info = send_log_to_group(f"✅ TEST LOG from Railway\n🕒 {time_str}")
    return jsonify(
        {
            "ok": ok,
            "target_group_id": TARGET_GROUP_ID,
            "has_bot_token": bool(BOT_TOKEN),
            "telegram_response": info,
        }
    ), (200 if ok else 500)


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

    ok, info = send_log_to_group(log_text)
    if not ok:
        # Чтобы ты видел причину в Railway (в ответе MiniApp это не мешает)
        print("TELEGRAM LOG ERROR:", info)

    return jsonify({"reply": reply})
   
@api.get("/test-log")
def test_log():
    send_log_to_group("✅ TEST: Railway API может писать в Telegram")
    return jsonify({"ok": True})