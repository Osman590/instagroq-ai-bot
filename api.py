import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, Tuple, Optional, List

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import base64

from groq_client import ask_groq

api = Flask(__name__)
CORS(api)

BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()
STABILITY_API_KEY = (os.getenv("STABILITY_API_KEY") or "").strip()

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


# =========================
# IMAGE GENERATION (STABILITY.AI) — ДОБАВЛЕНО
# =========================
@api.post("/api/image")
def api_image():
    if not STABILITY_API_KEY:
        return jsonify({"error": "stability_key_missing"}), 500

    form = request.form
    files = request.files

    tg_user_id = int(form.get("tg_user_id", 0))
    mode = form.get("mode", "txt2img")
    prompt = (form.get("prompt") or "").strip()

    access = get_access(tg_user_id)
    if access["is_blocked"]:
        return jsonify({"error": "blocked"}), 403
    if not access["is_free"]:
        return jsonify({"error": "payment_required"}), 402

    headers = {
        "Authorization": f"Bearer {STABILITY_API_KEY}",
        "Accept": "application/json",
    }

    try:
        if mode == "txt2img":
            r = requests.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                headers=headers,
                json={
                    "text_prompts": [{"text": prompt}],
                    "cfg_scale": 7,
                    "height": 1024,
                    "width": 1024,
                    "steps": 30,
                },
                timeout=60,
            )
        else:
            if "file" not in files:
                return jsonify({"error": "file_required"}), 400

            img = files["file"]
            r = requests.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/image-to-image",
                headers=headers,
                files={"init_image": img},
                data={
                    "text_prompts[0][text]": prompt,
                    "cfg_scale": "7",
                    "steps": "30",
                },
                timeout=60,
            )

        r.raise_for_status()
        data = r.json()
        img_b64 = data["artifacts"][0]["base64"]

        return jsonify({
            "image_base64": f"data:image/png;base64,{img_b64}",
            "eta_seconds": 20
        })

    except Exception as e:
        send_log_to_group(f"❌ Stability error: {e}")
        return jsonify({"error": "generation_failed"}), 500