from typing import Any, Dict

from flask import Flask, request, jsonify
from flask_cors import CORS

from groq_client import ask_groq
from logger import log_chat   # ✅ ДОБАВЛЕНО

# ---------- FLASK API ----------
api = Flask(__name__)
CORS(api)


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

      // (позже)
      "user_id": 123456789,
      "username": "nickname"
    }
    """
    data: Dict[str, Any] = request.get_json(silent=True) or {}

    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "empty"}), 400

    lang = data.get("lang") or "ru"
    style = data.get("style") or "steps"
    persona = data.get("persona") or "friendly"

    # 👇 пока может быть 0 / None — это нормально
    user_id = int(data.get("user_id") or 0)
    username = data.get("username")

    try:
        reply = ask_groq(
            text,
            lang=lang,
            style=style,
            persona=persona,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # ✅ ЛОГ В ГРУППУ TELEGRAM
    try:
        log_chat(
            user_id=user_id,
            username=username,
            user_text=text,
            ai_reply=reply,
        )
    except Exception:
        # логирование не должно ломать чат
        pass

    return jsonify({"reply": reply})