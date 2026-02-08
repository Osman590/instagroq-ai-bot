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

# ✅ Группа для логов (поддерживаем оба названия переменной)
LOG_GROUP_ID = os.getenv("LOG_GROUP_ID")
TARGET_GROUP_ID = os.getenv("TARGET_GROUP_ID")
GROUP_ID_RAW = (LOG_GROUP_ID or TARGET_GROUP_ID or "-4697406654").strip()

# ✅ Токен нужен, чтобы API мог отправлять сообщения в Telegram
BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()

# ✅ приводим chat_id к int (если криво — будет 0)
try:
    GROUP_ID = int(GROUP_ID_RAW)
except Exception:
    GROUP_ID = 0


def send_log_to_group(text: str) -> Tuple[bool, str]:
    """(ok, telegram_response_text)"""
    if not BOT_TOKEN:
        return False, "BOT_TOKEN is empty"
    if not GROUP_ID:
        return False, "LOG_GROUP_ID/TARGET_GROUP_ID is empty or invalid"

    # Telegram лимит ~4096 символов
    if len(text) > 3900:
        text = text[:3900] + "\n…(truncated)"

    try:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": GROUP_ID, "text": text},
            timeout=12,
        )
        return r.ok, r.text
    except Exception as e:
        return False, f"requests error: {e}"


def extract_last_user_message(raw: str) -> str:
    """
    Если в raw прилетел промпт/история (Conversation: ... User: ...),
    вытаскиваем только последнее сообщение пользователя.
    Иначе возвращаем raw как есть.
    """
    s = (raw or "").strip()
    if not s:
        return ""

    # Частые маркеры "простыни"
    if "Conversation:" in s or "\nUser:" in s or s.startswith("You are "):
        # Берём последнюю секцию после "User:"
        idx = s.rfind("User:")
        if idx != -1:
            s2 = s[idx + len("User:") :].strip()
            # отрезаем, если дальше идёт "Assistant:"
            cut = s2.find("\nAssistant:")
            if cut != -1:
                s2 = s2[:cut].strip()
            return s2

    return s


@api.get("/")
def root():
    return "ok"


@api.get("/health")
def health():
    return "ok"


@api.get("/api/test-log")
def test_log():
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ok, info = send_log_to_group(f"✅ TEST LOG from Railway\n🕒 {time_str}")
    return (
        jsonify(
            {
                "ok": ok,
                "group_id": GROUP_ID,
                "has_bot_token": bool(BOT_TOKEN),
                "telegram_response": info,
            }
        ),
        (200 if ok else 500),
    )


@api.post("/api/chat")
def api_chat():
    data: Dict[str, Any] = request.get_json(silent=True) or {}

    raw_text = (data.get("text") or "").strip()
    if not raw_text:
        return jsonify({"error": "empty"}), 400

    # ✅ ВАЖНО: логируем ТОЛЬКО последнее сообщение пользователя (без истории/инструкций)
    text = extract_last_user_message(raw_text)

    lang = data.get("lang") or "ru"
    style = data.get("style") or "steps"
    persona = data.get("persona") or "friendly"

    # данные от миниаппа (если передаст)
    tg_user_id = data.get("tg_user_id") or data.get("telegram_user_id") or "—"
    tg_username = data.get("tg_username") or data.get("username") or "—"
    tg_first_name = data.get("tg_first_name") or data.get("first_name") or "—"

    try:
        reply = ask_groq(text, lang=lang, style=style, persona=persona)
    except Exception as e:
        send_log_to_group(f"❌ Ошибка /api/chat: {e}")
        return jsonify({"error": str(e)}), 500

    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1) USER (одно сообщение)
    send_log_to_group(
        "🕒 " + time_str + "\n"
        f"👤 {tg_first_name} (@{tg_username})\n"
        f"🆔 {tg_user_id}\n"
        f"💬 {text}"
    )

    # 2) AI (второе сообщение)
    send_log_to_group(
        "🤖 ИИ\n"
        f"{reply}"
    )

    return jsonify({"reply": reply})