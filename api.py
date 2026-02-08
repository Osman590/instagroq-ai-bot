import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, Tuple

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

from groq_client import ask_groq

api = Flask(__name__)
CORS(api)

BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()

# Группа для логов: сначала TARGET_GROUP_ID, потом LOG_GROUP_ID
GROUP_ID_RAW = (os.getenv("TARGET_GROUP_ID") or os.getenv("LOG_GROUP_ID") or "0").strip()
try:
    GROUP_ID = int(GROUP_ID_RAW)
except Exception:
    GROUP_ID = 0

# --- SQLite (простая база прав) ---
DB_PATH = os.getenv("ACCESS_DB_PATH") or "access.db"


def db_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def db_init():
    con = db_conn()
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS access (
            user_id INTEGER PRIMARY KEY,
            is_free INTEGER DEFAULT 0,
            is_blocked INTEGER DEFAULT 0,
            updated_at TEXT
        )
        """
    )
    con.commit()
    con.close()


db_init()


def set_free(user_id: int, value: bool) -> None:
    con = db_conn()
    cur = con.cursor()
    cur.execute(
        """
        INSERT INTO access (user_id, is_free, is_blocked, updated_at)
        VALUES (?, ?, COALESCE((SELECT is_blocked FROM access WHERE user_id=?), 0), ?)
        ON CONFLICT(user_id) DO UPDATE SET
            is_free=excluded.is_free,
            updated_at=excluded.updated_at
        """,
        (user_id, 1 if value else 0, user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    con.commit()
    con.close()


def set_blocked(user_id: int, value: bool) -> None:
    con = db_conn()
    cur = con.cursor()
    cur.execute(
        """
        INSERT INTO access (user_id, is_free, is_blocked, updated_at)
        VALUES (?, COALESCE((SELECT is_free FROM access WHERE user_id=?), 0), ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            is_blocked=excluded.is_blocked,
            updated_at=excluded.updated_at
        """,
        (user_id, user_id, 1 if value else 0, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    con.commit()
    con.close()


def get_access(user_id: int) -> Dict[str, Any]:
    con = db_conn()
    cur = con.cursor()
    cur.execute("SELECT is_free, is_blocked, updated_at FROM access WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    con.close()
    if not row:
        return {"user_id": user_id, "is_free": False, "is_blocked": False, "updated_at": None}
    return {"user_id": user_id, "is_free": bool(row[0]), "is_blocked": bool(row[1]), "updated_at": row[2]}


def send_log_to_group(text: str) -> Tuple[bool, str]:
    if not BOT_TOKEN:
        return False, "BOT_TOKEN is empty"
    if not GROUP_ID:
        return False, "TARGET_GROUP_ID/LOG_GROUP_ID is empty or invalid"

    # Telegram limit ~4096
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
            s2 = s[idx + len("User:") :].strip()
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
    ok, info = send_log_to_group(f"✅ TEST LOG\n🕒 {time_str}")
    return jsonify(
        {
            "ok": ok,
            "group_id": GROUP_ID,
            "has_bot_token": bool(BOT_TOKEN),
            "telegram_response": info,
        }
    ), (200 if ok else 500)


# Для проверки доступа с миниаппа
@api.get("/api/access/<int:user_id>")
def api_access(user_id: int):
    return jsonify(get_access(user_id))


@api.post("/api/chat")
def api_chat():
    data: Dict[str, Any] = request.get_json(silent=True) or {}

    raw_text = (data.get("text") or "").strip()
    if not raw_text:
        return jsonify({"error": "empty"}), 400

    text = extract_last_user_message(raw_text)

    # user data
    tg_user_id = data.get("tg_user_id") or data.get("telegram_user_id") or 0
    try:
        tg_user_id_int = int(tg_user_id)
    except Exception:
        tg_user_id_int = 0

    tg_username = data.get("tg_username") or data.get("username") or "—"
    tg_first_name = data.get("tg_first_name") or data.get("first_name") or "—"

    # --- ACCESS CHECK ---
    if tg_user_id_int:
        a = get_access(tg_user_id_int)
        if a["is_blocked"]:
            return jsonify({"error": "blocked"}), 403
        if not a["is_free"]:
            # платно по умолчанию
            return jsonify({"error": "payment_required"}), 402
    else:
        # если юзер айди вообще не передали — считаем платно
        return jsonify({"error": "payment_required"}), 402

    lang = data.get("lang") or "ru"
    style = data.get("style") or "steps"
    persona = data.get("persona") or "friendly"

    try:
        reply = ask_groq(text, lang=lang, style=style, persona=persona)
    except Exception as e:
        send_log_to_group(f"❌ Ошибка /api/chat: {e}")
        return jsonify({"error": str(e)}), 500

    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ОДНО сообщение: время + пользователь + сообщение + ответ
    send_log_to_group(
        f"🕒 {time_str}\n"
        f"👤 {tg_first_name} (@{tg_username})\n"
        f"🆔 {tg_user_id_int}\n"
        f"💬 {text}\n\n"
        f"🤖 {reply}"
    )

    return jsonify({"reply": reply})