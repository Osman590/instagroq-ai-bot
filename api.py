import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

from groq_client import ask_groq

api = Flask(__name__)
CORS(api)

TARGET_GROUP_ID = int(os.getenv("TARGET_GROUP_ID") or "-4697406654")
BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()

DB_PATH = os.getenv("ACCESS_DB_PATH") or "access.db"


def _now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_access(
          user_id INTEGER PRIMARY KEY,
          free_until INTEGER,
          blocked_until INTEGER,
          updated_at INTEGER
        )
        """
    )
    conn.commit()
    return conn


def _get_access(user_id: int) -> Tuple[bool, bool]:
    """
    returns: (is_free, is_blocked)
    """
    now = _now_ts()
    with _db() as conn:
        row = conn.execute(
            "SELECT free_until, blocked_until FROM user_access WHERE user_id=?",
            (user_id,),
        ).fetchone()

    free_until = row[0] if row else None
    blocked_until = row[1] if row else None

    is_free = (free_until == -1) or (isinstance(free_until, int) and free_until > now)
    is_blocked = (blocked_until == -1) or (isinstance(blocked_until, int) and blocked_until > now)

    return is_free, is_blocked


def send_log_to_group(text: str) -> None:
    if not BOT_TOKEN or not TARGET_GROUP_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": TARGET_GROUP_ID, "text": text},
            timeout=12,
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
    data: Dict[str, Any] = request.get_json(silent=True) or {}

    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "empty"}), 400

    lang = data.get("lang") or "ru"
    style = data.get("style") or "steps"
    persona = data.get("persona") or "friendly"

    # ✅ принимаем оба формата ключей, чтобы не ломать фронт
    tg_user_id = data.get("tg_user_id") or data.get("telegram_user_id") or data.get("telegramUserId")
    tg_username = data.get("tg_username") or data.get("username") or "—"
    tg_first_name = data.get("tg_first_name") or data.get("first_name") or "—"

    if not tg_user_id:
        # без user_id нельзя управлять доступом
        return jsonify({"error": "no_telegram_user"}), 403

    try:
        tg_user_id_int = int(tg_user_id)
    except Exception:
        return jsonify({"error": "bad_telegram_user"}), 400

    is_free, is_blocked = _get_access(tg_user_id_int)

    if is_blocked:
        return jsonify({"error": "blocked"}), 403

    # ✅ пока оплата не подключена — доступ по умолчанию платный
    if not is_free:
        return jsonify({"error": "paid_required"}), 402

    # --- AI ---
    try:
        reply = ask_groq(text, lang=lang, style=style, persona=persona)
    except Exception as e:
        send_log_to_group(f"❌ Ошибка /api/chat: {e}")
        return jsonify({"error": str(e)}), 500

    # --- LOG (одно сообщение: user + ai) ---
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_text = (
        "🧩 Mini App чат\n"
        f"🕒 {time_str}\n"
        f"👤 {tg_first_name} (@{tg_username})\n"
        f"🆔 user_id: {tg_user_id_int}\n\n"
        f"💬 {text}\n\n"
        f"🤖 {reply}"
    )
    send_log_to_group(log_text)

    return jsonify({"reply": reply})