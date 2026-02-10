# api.py
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

GROUP_ID_RAW = (os.getenv("TARGET_GROUP_ID") or os.getenv("LOG_GROUP_ID") or "0").strip()
try:
    GROUP_ID = int(GROUP_ID_RAW)
except Exception:
    GROUP_ID = 0

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
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT
        )
        """
    )
    con.commit()
    con.close()


db_init()


def _ensure_columns():
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
# ACCESS
# =========================
def get_access(user_id: int) -> Dict[str, Any]:
    con = db_conn()
    cur = con.cursor()
    cur.execute(
        "SELECT is_free, is_blocked FROM access WHERE user_id=?",
        (user_id,),
    )
    row = cur.fetchone()
    con.close()
    if not row:
        return {"is_free": False, "is_blocked": False}
    return {"is_free": bool(row[0]), "is_blocked": bool(row[1])}


# =========================
# MEMORY
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
    rows.reverse()
    return [{"role": r[0], "text": r[1]} for r in rows]


def build_memory_prompt(history: List[Dict[str, str]], user_text: str) -> str:
    lines = ["Conversation:"]
    if history:
        for m in history:
            role = "User" if m["role"] == "user" else "Assistant"
            lines.append(f"{role}: {m['text']}")
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


@api.post("/api/chat")
def api_chat():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    tg_user_id = int(data.get("tg_user_id") or 0)

    access = get_access(tg_user_id)
    if access["is_blocked"]:
        return jsonify({"error": "blocked"}), 403
    if not access["is_free"]:
        return jsonify({"error": "payment_required"}), 402

    history = mem_get(tg_user_id)
    prompt = build_memory_prompt(history, text)

    mem_add(tg_user_id, "user", text)
    reply = ask_groq(prompt)
    mem_add(tg_user_id, "assistant", reply)

    return jsonify({"reply": reply})


# =========================
# ✅ STABILITY AI IMAGE
# =========================
@api.post("/api/image")
def api_image():
    if not STABILITY_API_KEY:
        return jsonify({"error": "STABILITY_API_KEY missing"}), 500

    tg_user_id = int(request.form.get("tg_user_id") or 0)
    access = get_access(tg_user_id)
    if access["is_blocked"]:
        return jsonify({"error": "blocked"}), 403
    if not access["is_free"]:
        return jsonify({"error": "payment_required"}), 402

    prompt = request.form.get("prompt") or ""
    mode = request.form.get("mode") or "txt2img"
    image_file = request.files.get("image")

    headers = {
        "Authorization": f"Bearer {STABILITY_API_KEY}",
        "Accept": "application/json",
    }

    try:
        if mode == "txt2img":
            r = requests.post(
                "https://api.stability.ai/v2beta/stable-image/generate/core",
                headers=headers,
                files={"none": ""},
                data={"prompt": prompt},
                timeout=60,
            )

        elif mode in ("img2img", "inpaint"):
            if not image_file:
                return jsonify({"error": "image_required"}), 400
            r = requests.post(
                "https://api.stability.ai/v2beta/stable-image/edit",
                headers=headers,
                files={"image": image_file},
                data={"prompt": prompt},
                timeout=60,
            )

        elif mode == "remove_bg":
            if not image_file:
                return jsonify({"error": "image_required"}), 400
            r = requests.post(
                "https://api.stability.ai/v2beta/stable-image/remove-background",
                headers=headers,
                files={"image": image_file},
                timeout=60,
            )

        elif mode == "upscale":
            if not image_file:
                return jsonify({"error": "image_required"}), 400
            r = requests.post(
                "https://api.stability.ai/v2beta/stable-image/upscale",
                headers=headers,
                files={"image": image_file},
                timeout=60,
            )

        else:
            return jsonify({"error": "unknown_mode"}), 400

        if not r.ok:
            return jsonify({"error": r.text}), 500

        data = r.json()
        img_base64 = data["image"] if "image" in data else data["images"][0]["base64"]

        return jsonify({"image_base64": f"data:image/png;base64,{img_base64}"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500