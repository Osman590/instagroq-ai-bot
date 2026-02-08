from typing import Any, Dict

from flask import Flask, request, jsonify
from flask_cors import CORS

from groq_client import ask_groq

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

    try:
        reply = ask_groq(
            text,
            lang=lang,
            style=style,
            persona=persona,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"reply": reply})