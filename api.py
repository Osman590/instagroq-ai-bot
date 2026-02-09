import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, Tuple, Optional, List

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
            updated_at TEXT,
            last_menu_chat_id INTEGER,
            last_menu_message_id INTEGER
        )
        """
    )
    # ✅ память чата
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,               -- "user" | "assistant"
            text TEXT NOT NULL,
            created_at TEXT
        )
        """
    )
    con.commit()
    con.close()


db_init()


def _ensure_columns():
    """На случай если таблица была создана раньше без колонок меню."""
    con = db_conn()
    cur = con.cursor()
    try:
        cur.execute("ALTER TABLE access ADD COLUMN last_menu_chat_id INTEGER")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE access ADD COLUMN last_menu_message_id INTEGER")
    except Exception:
        pass
    con.commit()
    con.close()


_ensure_columns()


# =========================
# ACCESS (как было)
# =========================
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
    cur.execute(
        "SELECT is_free, is_blocked, updated_at, last_menu_chat_id, last_menu_message_id FROM access WHERE user_id=?",
        (user_id,),
    )
    row = cur.fetchone()
    con.close()
    if not row:
        return {
            "user_id": user_id,
            "is_free": False,
            "is_blocked": False,
            "updated_at": None,
            "last_menu_chat_id": None,
            "last_menu_message_id": None,
        }
    return {
        "user_id": user_id,
        "is_free": bool(row[0]),
        "is_blocked": bool(row[1]),
        "updated_at": row[2],
        "last_menu_chat_id": row[3],
        "last_menu_message_id": row[4],
    }


def set_last_menu(user_id: int, chat_id: int, message_id: int) -> None:
    con = db_conn()
    cur = con.cursor()
    cur.execute(
        """
        INSERT INTO access (user_id, is_free, is_blocked, updated_at, last_menu_chat_id, last_menu_message_id)
        VALUES (?, COALESCE((SELECT is_free FROM access WHERE user_id=?), 0),
                COALESCE((SELECT is_blocked FROM access WHERE user_id=?), 0),
                ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            last_menu_chat_id=excluded.last_menu_chat_id,
            last_menu_message_id=excluded.last_menu_message_id,
            updated_at=excluded.updated_at
        """,
        (
            user_id,
            user_id,
            user_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            chat_id,
            message_id,
        ),
    )
    con.commit()
    con.close()


def clear_last_menu(user_id: int) -> None:
    con = db_conn()
    cur = con.cursor()
    cur.execute(
        """
        UPDATE access
        SET last_menu_chat_id=NULL, last_menu_message_id=NULL, updated_at=?
        WHERE user_id=?
        """,
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id),
    )
    con.commit()
    con.close()


def get_last_menu(user_id: int) -> Tuple[Optional[int], Optional[int]]:
    a = get_access(user_id)
    return a.get("last_menu_chat_id"), a.get("last_menu_message_id")


# =========================
# LOG (как было)
# =========================
def send_log_to_group(text: str) -> Tuple[bool, str]:
    if not BOT_TOKEN:
        return False, "BOT_TOKEN is empty"
    if not GROUP_ID:
        return False, "TARGET_GROUP_ID/LOG_GROUP_ID is empty or invalid"

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


# =========================
# ✅ MEMORY (новое)
# =========================
def mem_add(user_id: int, role: str, text: str) -> None:
    con = db_conn()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO chat_memory (user_id, role, text, created_at) VALUES (?, ?, ?, ?)",
        (user_id, role, text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    con.commit()
    con.close()


def mem_get(user_id: int, limit: int = 24) -> List[Dict[str, str]]:
    con = db_conn()
    cur = con.cursor()
    cur.execute(
        """
        SELECT role, text
        FROM chat_memory
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    rows = cur.fetchall()
    con.close()
    rows.reverse()  # в правильный порядок (старые -> новые)
    out = []
    for r in rows:
        out.append({"role": r[0], "text": r[1]})
    return out


def mem_clear(user_id: int) -> None:
    con = db_conn()
    cur = con.cursor()
    cur.execute("DELETE FROM chat_memory WHERE user_id=?", (user_id,))
    con.commit()
    con.close()


def build_memory_prompt(history: List[Dict[str, str]], user_text: str) -> str:
    lines = []
    lines.append("Conversation:")
    if history:
        for m in history:
            role = "User" if m.get("role") == "user" else "Assistant"
            lines.append(f"{role}: {m.get('text','')}")
    else:
        lines.append("(empty)")
    lines.append("")
    lines.append(f"User: {user_text}")
    lines.append("Assistant:")
    return "\n".join(lines)


# =========================
# ROUTES
# =========================
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


@api.get("/api/access/<int:user_id>")
def api_access(user_id: int):
    return jsonify(get_access(user_id))


# ✅ очистка памяти по кнопке "Очистить"
@api.post("/api/memory/clear")
def api_memory_clear():
    data: Dict[str, Any] = request.get_json(silent=True) or {}
    tg_user_id = data.get("tg_user_id") or 0
    try:
        tg_user_id_int = int(tg_user_id)
    except Exception:
        tg_user_id_int = 0

    if not tg_user_id_int:
        return jsonify({"error": "bad_user_id"}), 400

    # доступ как в чате
    a = get_access(tg_user_id_int)
    if a["is_blocked"]:
        return jsonify({"error": "blocked"}), 403
    if not a["is_free"]:
        return jsonify({"error": "payment_required"}), 402

    mem_clear(tg_user_id_int)
    return jsonify({"ok": True})


@api.post("/api/chat")
def api_chat():
    data: Dict[str, Any] = request.get_json(silent=True) or {}

    raw_text = (data.get("text") or "").strip()
    if not raw_text:
        return jsonify({"error": "empty"}), 400

    text = extract_last_user_message(raw_text)

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
            return jsonify({"error": "payment_required"}), 402
    else:
        return jsonify({"error": "payment_required"}), 402

    lang = data.get("lang") or "ru"
    style = data.get("style") or "steps"
    persona = data.get("persona") or "friendly"

    # ✅ берём историю + строим промпт с памятью
    history = mem_get(tg_user_id_int, limit=24)
    prompt_with_memory = build_memory_prompt(history, text)

    # ✅ сохраняем user сообщение в память ДО ответа
    mem_add(tg_user_id_int, "user", text)

    try:
        reply = ask_groq(prompt_with_memory, lang=lang, style=style, persona=persona)
    except Exception as e:
        send_log_to_group(f"❌ Ошибка /api/chat: {e}")
        return jsonify({"error": str(e)}), 500

    # ✅ сохраняем ответ в память
    mem_add(tg_user_id_int, "assistant", reply)

    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    send_log_to_group(
        f"🕒 {time_str}\n"
        f"👤 {tg_first_name} (@{tg_username})\n"
        f"🆔 {tg_user_id_int}\n"
        f"💬 {text}\n\n"
        f"🤖 {reply}"
    )

    return jsonify({"reply": reply})