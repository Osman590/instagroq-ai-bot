import os
import json
from datetime import datetime
from typing import Any, Dict, Tuple

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

from groq_client import ask_groq

api = Flask(__name__)
CORS(api)

# ✅ Группа для логов (поддерживаем оба названия переменной)
LOG_GROUP_ID = os.getenv("LOG_GROUP_ID")
TARGET_GROUP_ID = os.getenv("TARGET_GROUP_ID")
GROUP_ID_RAW = (LOG_GROUP_ID or TARGET_GROUP_ID or "0").strip()

BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()

try:
    GROUP_ID = int(GROUP_ID_RAW)
except Exception:
    GROUP_ID = 0

ACCESS_FILE = "access.json"


def load_access() -> Dict[str, Any]:
    try:
        with open(ACCESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}


def get_user_access(user_id: int) -> Dict[str, Any]:
    db = load_access()
    return db.get(str(user_id), {"paid": False, "free": False, "blocked": False})


def has_access(user_id: int) -> bool:
    if not user_id:
        return False
    st = get_user_access(int(user_id))
    if st.get("blocked"):
        return False
    return bool(st.get("paid") or st.get("free"))


def send_log_to_group(text: str) -> Tuple[bool, str]:
    if not BOT_TOKEN:
        return False, "BOT_TOKEN is empty"
    if not GROUP_ID:
        return False, "LOG_GROUP_ID/TARGET_GROUP_ID is empty or invalid"

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
    s = (raw or "").strip()
    if not s:
        return ""
    if "Conversation:" in s or "\nUser:" in s or s.startswith("You are "):
        idx = s.rfind("User:")
        if idx != -1:
            s2 = s[idx + len("User:"):].strip()
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

    text = extract_last_user_message(raw_text)

    lang = data.get("lang") or "ru"
    style = data.get("style") or "steps"
    persona = data.get("persona") or "friendly"

    tg_user_id = data.get("tg_user_id") or data.get("telegram_user_id") or 0
    try:
        tg_user_id_int = int(tg_user_id)
    except Exception:
        tg_user_id_int = 0

    tg_username = data.get("tg_username") or data.get("username") or "—"
    tg_first_name = data.get("tg_first_name") or data.get("first_name") or "—"

    # 🔐 ДОСТУП: по умолчанию платно
    if not has_access(tg_user_id_int):
        return jsonify({"error": "payment_required", "message": "Нужно купить пакет"}), 402

    try:
        reply = ask_groq(text, lang=lang, style=style, persona=persona)
    except Exception as e:
        send_log_to_group(f"❌ Ошибка /api/chat: {e}")
        return jsonify({"error": str(e)}), 500

    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ✅ ОДНО сообщение (как ты хочешь): время + пользователь + сообщение + ИИ + ответ
    send_log_to_group(
        f"🕒 {time_str}\n"
        f"👤 {tg_first_name} (@{tg_username})\n"
        f"🆔 {tg_user_id_int}\n"
        f"💬 {text}\n\n"
        f"🤖 ИИ\n{reply}"
    )

    return jsonify({"reply": reply})