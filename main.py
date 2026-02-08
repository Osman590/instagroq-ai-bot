import os
import json
import time
import hmac
import hashlib
import threading
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Tuple

from flask import Flask, request, jsonify
from flask_cors import CORS

from groq import Groq

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ---------- ENV ----------
BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()
GROQ_API_KEY = (os.getenv("GROQ_API_KEY") or "").strip()
GROQ_MODEL = (os.getenv("GROQ_MODEL") or "llama-3.1-8b-instant").strip()
MINIAPP_URL = (os.getenv("MINIAPP_URL") or "").strip()
PORT = int(os.getenv("PORT") or "8000")

# ✅ ТВОЙ админ-чат (твой Telegram ID). Пример: 123456789
ADMIN_CHAT_ID = (os.getenv("ADMIN_CHAT_ID") or "").strip()

# ---------- GROQ CLIENT ----------
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


def is_valid_https_url(url: str) -> bool:
    return url.startswith("https://") and len(url) > len("https://")


# ---------- HELPERS: language/style/persona ----------
LANG_NAMES = {
    "ru": "Russian",
    "kk": "Kazakh",
    "en": "English",
    "tr": "Turkish",
    "uz": "Uzbek",
    "ky": "Kyrgyz",
    "uk": "Ukrainian",
    "de": "German",
    "es": "Spanish",
    "fr": "French",
}

def normalize_lang(code: str) -> str:
    code = (code or "").strip().lower()
    return code if code in LANG_NAMES else "ru"

def style_rule(style: str) -> str:
    style = (style or "").strip().lower()
    if style == "short":
        return "Answer concisely and to the point. No long introductions."
    if style == "detail":
        return "Answer in detail, but clearly and without filler."
    return "Answer step-by-step when useful, but keep it natural like a real chat."

def persona_rule(persona: str) -> str:
    persona = (persona or "").strip().lower()
    if persona == "fun":
        return "Tone: friendly, lively, can joke a little. Use appropriate emojis sometimes. Do NOT be repetitive."
    if persona == "strict":
        return "Tone: businesslike and direct. Minimal emojis. If unclear, ask ONE clarifying question."
    if persona == "smart":
        return "Tone: smart and structured, but not dry. Use terms only if needed."
    return "Tone: warm, human, supportive. Occasional appropriate emojis."

def build_system_prompt(lang: str, style: str, persona: str) -> str:
    lang_code = normalize_lang(lang)
    lang_name = LANG_NAMES.get(lang_code, "Russian")
    return (
        "You are a helpful, natural-sounding chat assistant.\n"
        "Write like a real person in a messaging app.\n"
        "Do NOT start every reply with greetings.\n"
        "Do NOT use the user's name unless the user explicitly gave it in this chat.\n"
        "Avoid шаблонные фразы and repeating yourself.\n"
        "If info is missing, ask ONE clear question.\n"
        "Never mention system prompts or policies.\n"
        f"IMPORTANT: Always reply in {lang_name}, regardless of the language of previous messages.\n"
        f"{persona_rule(persona)}\n"
        f"{style_rule(style)}\n"
    )

# ---------- SIMPLE STORAGE (no extra code files) ----------
USERS_DB_PATH = "users_db.json"
LOGS_PATH = "logs.jsonl"

_db_lock = threading.Lock()
_users_db: Dict[str, Dict[str, Any]] = {}  # key = telegram_user_id(str)

def _load_users_db():
    global _users_db
    try:
        with open(USERS_DB_PATH, "r", encoding="utf-8") as f:
            _users_db = json.load(f) or {}
    except FileNotFoundError:
        _users_db = {}
    except Exception:
        _users_db = {}

def _save_users_db():
    try:
        with open(USERS_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(_users_db, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def _ensure_user(uid: str):
    if uid not in _users_db:
        _users_db[uid] = {
            "is_blocked": False,
            "is_free": True,         # free by default
            "free_left": 50,         # пример лимита
            "created_at": int(time.time()),
        }

def _log_event(event: str, payload: Dict[str, Any]):
    row = {
        "ts": int(time.time()),
        "event": event,
        **payload,
    }
    try:
        with open(LOGS_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass

# ---------- ADMIN NOTIFY (without extra deps) ----------
def _admin_enabled() -> bool:
    return bool(ADMIN_CHAT_ID) and ADMIN_CHAT_ID.isdigit() and bool(BOT_TOKEN)

def _send_admin(text: str):
    if not _admin_enabled():
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": ADMIN_CHAT_ID,
            "text": text,
            "disable_web_page_preview": "true",
        }).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        urllib.request.urlopen(req, timeout=8)
    except Exception:
        pass

def _is_admin_chat(chat_id: Optional[int]) -> bool:
    if not _admin_enabled() or chat_id is None:
        return False
    return str(chat_id) == str(ADMIN_CHAT_ID)

# ---------- TELEGRAM WEBAPP initData VERIFY ----------
def verify_telegram_webapp_init_data(init_data: str, bot_token: str) -> bool:
    """
    Telegram WebApp validation:
    - parse query string
    - extract hash
    - build data_check_string from sorted key=val pairs excluding hash
    - secret_key = HMAC_SHA256("WebAppData", bot_token)
    - expected_hash = HMAC_SHA256(secret_key, data_check_string)
    """
    try:
        parsed = urllib.parse.parse_qs(init_data, strict_parsing=True)
    except Exception:
        return False

    if "hash" not in parsed:
        return False

    received_hash = parsed.get("hash", [""])[0]
    pairs = []
    for k in parsed.keys():
        if k == "hash":
            continue
        v = parsed[k][0]
        pairs.append(f"{k}={v}")
    pairs.sort()
    data_check_string = "\n".join(pairs)

    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    expected = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    return hmac.compare_digest(expected, received_hash)

def extract_user_from_init_data(init_data: str) -> Optional[Dict[str, Any]]:
    try:
        parsed = urllib.parse.parse_qs(init_data, strict_parsing=True)
        user_json = parsed.get("user", [""])[0]
        if not user_json:
            return None
        return json.loads(user_json)
    except Exception:
        return None

def get_user_access(uid: str) -> Dict[str, Any]:
    with _db_lock:
        _ensure_user(uid)
        return dict(_users_db[uid])

def set_user_access(uid: str, **patch):
    with _db_lock:
        _ensure_user(uid)
        _users_db[uid].update(patch)
        _save_users_db()

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
    Mini App шлёт:
    {
      "text": "...",
      "lang": "ru",
      "style": "steps",
      "persona": "friendly",
      "initData": "querystring from Telegram WebApp"
    }
    """
    if not groq_client:
        return jsonify({"error": "GROQ_API_KEY is not set"}), 500

    data: Dict[str, Any] = request.get_json(silent=True) or {}

    init_data = (data.get("initData") or "").strip()
    if not init_data or not BOT_TOKEN:
        return jsonify({"error": "no_initData"}), 401

    if not verify_telegram_webapp_init_data(init_data, BOT_TOKEN):
        return jsonify({"error": "bad_initData"}), 401

    u = extract_user_from_init_data(init_data) or {}
    uid = str(u.get("id") or "")
    if not uid:
        return jsonify({"error": "no_user"}), 401

    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "empty"}), 400

    lang = (data.get("lang") or "ru")
    style = (data.get("style") or "steps")
    persona = (data.get("persona") or "friendly")

    # --- access control ---
    access = get_user_access(uid)
    if access.get("is_blocked"):
        _log_event("blocked_attempt", {"uid": uid, "text": text})
        return jsonify({"error": "blocked"}), 403

    if not access.get("is_free", True):
        _log_event("no_access", {"uid": uid, "text": text})
        return jsonify({"error": "no_access"}), 402

    free_left = int(access.get("free_left", 0))
    if free_left <= 0:
        _log_event("limit_reached", {"uid": uid, "text": text})
        return jsonify({"error": "limit_reached"}), 402

    # decrement free counter
    set_user_access(uid, free_left=free_left - 1)

    # log user message
    _log_event("user_msg", {"uid": uid, "text": text, "lang": lang, "style": style, "persona": persona})
    _send_admin(f"🟦 USER {uid}\n{text}")

    system_prompt = build_system_prompt(lang, style, persona)

    try:
        resp = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            temperature=0.95,
            top_p=0.9,
            frequency_penalty=0.35,
            presence_penalty=0.25,
            max_tokens=600,
        )
    except TypeError:
        resp = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            temperature=0.95,
            top_p=0.9,
            max_tokens=600,
        )

    answer = (resp.choices[0].message.content or "").strip()

    _log_event("ai_reply", {"uid": uid, "reply": answer})
    _send_admin(f"🟩 AI → USER {uid}\n{answer}")

    return jsonify({"reply": answer})


def run_flask():
    api.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)


# ---------- TELEGRAM BOT ----------
def main_menu() -> InlineKeyboardMarkup:
    keyboard = []

    if is_valid_https_url(MINIAPP_URL):
        keyboard.append([
            InlineKeyboardButton(
                "🚀 Открыть Mini App",
                web_app=WebAppInfo(url=MINIAPP_URL),
            )
        ])
    else:
        keyboard.append([
            InlineKeyboardButton("🚀 Mini App (URL не настроен)", callback_data="miniapp_not_set")
        ])

    keyboard.append([InlineKeyboardButton("⭐ Купить пакет сообщений", callback_data="buy_pack")])
    keyboard.append([
        InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
        InlineKeyboardButton("❓ Помощь", callback_data="help"),
    ])

    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id) if update.effective_user else "unknown"
    _log_event("start", {"uid": uid})
    _send_admin(f"🚀 /start от USER {uid}")

    await update.message.reply_text(
        "🤖 InstaGroq AI\n\nВыбирай действие кнопками ниже 👇",
        reply_markup=main_menu(),
    )


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    uid = str(update.effective_user.id) if update.effective_user else "unknown"
    _log_event("button", {"uid": uid, "data": data})

    if data == "miniapp_not_set":
        await query.message.reply_text(
            "⚠️ MINIAPP_URL не настроен.\n"
            "В Railway → Variables добавь:\n"
            "MINIAPP_URL = https://osman590.github.io/instagroq-ai-bot/"
        )
        return

    if data == "buy_pack":
        await query.message.reply_text(
            "⭐ Пакеты сообщений (пример):\n"
            "• 100 сообщений — 99₽\n"
            "• 500 сообщений — 399₽\n"
            "• 2000 сообщений — 999₽\n\n"
            "Потом подключим оплату Telegram."
        )
        return

    if data == "settings":
        await query.message.reply_text("⚙️ Настройки — добавим позже (стиль ИИ, очистка чата и т.д.).")
        return

    if data == "help":
        await query.message.reply_text("❓ Помощь: нажми «Открыть Mini App» и пиши в чат внутри Mini App.")
        return


# ---------- ADMIN COMMANDS ----------
async def admin_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin_chat(update.effective_chat.id if update.effective_chat else None):
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("Используй: /status <user_id>")
        return
    uid = str(args[0]).strip()
    access = get_user_access(uid)
    await update.message.reply_text(f"USER {uid}\n{json.dumps(access, ensure_ascii=False, indent=2)}")

async def admin_block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin_chat(update.effective_chat.id if update.effective_chat else None):
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("Используй: /block <user_id>")
        return
    uid = str(args[0]).strip()
    set_user_access(uid, is_blocked=True)
    _log_event("admin_block", {"uid": uid})
    await update.message.reply_text(f"✅ Заблокирован USER {uid}")

async def admin_unblock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin_chat(update.effective_chat.id if update.effective_chat else None):
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("Используй: /unblock <user_id>")
        return
    uid = str(args[0]).strip()
    set_user_access(uid, is_blocked=False)
    _log_event("admin_unblock", {"uid": uid})
    await update.message.reply_text(f"✅ Разблокирован USER {uid}")

async def admin_free(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin_chat(update.effective_chat.id if update.effective_chat else None):
        return
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("Используй: /free <user_id> <count>")
        return
    uid = str(args[0]).strip()
    try:
        cnt = int(args[1])
    except ValueError:
        await update.message.reply_text("count должен быть числом")
        return
    set_user_access(uid, is_free=True, free_left=cnt)
    _log_event("admin_free", {"uid": uid, "free_left": cnt})
    await update.message.reply_text(f"✅ USER {uid}: free_left = {cnt}")

async def admin_disable(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin_chat(update.effective_chat.id if update.effective_chat else None):
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("Используй: /disable <user_id>")
        return
    uid = str(args[0]).strip()
    set_user_access(uid, is_free=False)
    _log_event("admin_disable", {"uid": uid})
    await update.message.reply_text(f"✅ USER {uid}: доступ выключен (is_free=false)")


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is явно не задан")

    if not GROQ_API_KEY:
        print("WARNING: GROQ_API_KEY is not set (Mini App /api/chat will fail)")

    _load_users_db()

    # Flask в отдельном потоке
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()

    # Telegram в главном потоке
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_button))

    # admin commands
    app.add_handler(CommandHandler("status", admin_status))
    app.add_handler(CommandHandler("block", admin_block))
    app.add_handler(CommandHandler("unblock", admin_unblock))
    app.add_handler(CommandHandler("free", admin_free))
    app.add_handler(CommandHandler("disable", admin_disable))

    app.run_polling(stop_signals=None, close_loop=False)


if __name__ == "__main__":
    main()