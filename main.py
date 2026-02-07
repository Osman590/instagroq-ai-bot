import os
import threading
from typing import Any, Dict

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

# ✅ ВАЖНО: это URL ФРОНТА (GitHub Pages), а не Railway домен
MINIAPP_URL = (os.getenv("MINIAPP_URL") or "").strip()

# ✅ Railway сам задаёт PORT (часто 8080). На всякий случай есть fallback.
PORT = int(os.getenv("PORT") or "8000")


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
    # Ключ: НЕ фиксируем русский. Фиксируем язык = выбранный пользователем.
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
    Mini App будет слать сюда:
    { "text": "...", "lang": "en", "style": "steps", "persona": "fun" }
    Ответ:
    { "reply": "..." }
    """
    if not groq_client:
        return jsonify({"error": "GROQ_API_KEY is not set"}), 500

    data: Dict[str, Any] = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "empty"}), 400

    lang = (data.get("lang") or "ru")
    style = (data.get("style") or "steps")
    persona = (data.get("persona") or "friendly")

    system_prompt = build_system_prompt(lang, style, persona)

    try:
        resp = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            # ✅ параметры "живости"
            temperature=0.95,
            top_p=0.9,
            # ✅ меньше повторов/шаблонов
            frequency_penalty=0.35,
            presence_penalty=0.25,
            max_tokens=600,
        )
    except TypeError:
        # на случай если в твоей версии SDK не поддерживаются frequency/presence_penalty
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

    answer = resp.choices[0].message.content or ""
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
    await update.message.reply_text(
        "🤖 InstaGroq AI\n\nВыбирай действие кнопками ниже 👇",
        reply_markup=main_menu(),
    )


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""

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


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    if not GROQ_API_KEY:
        print("WARNING: GROQ_API_KEY is not set (Mini App /api/chat will fail)")

    # Flask в отдельном потоке
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()

    # Telegram в главном потоке
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_button))

    app.run_polling(stop_signals=None, close_loop=False)


if __name__ == "__main__":
    main()