import os
import json
from datetime import datetime
from typing import Dict, Any

import requests
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
    MessageHandler,
    filters,
)

# ---------- ENV ----------
BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()
MINIAPP_URL = (os.getenv("MINIAPP_URL") or "").strip()

# ✅ поддерживаем оба названия переменной (как у тебя было)
LOG_GROUP_ID_RAW = (os.getenv("LOG_GROUP_ID") or os.getenv("TARGET_GROUP_ID") or "0").strip()
try:
    LOG_GROUP_ID = int(LOG_GROUP_ID_RAW)
except Exception:
    LOG_GROUP_ID = 0

# ✅ username бота (без @)
BOT_USERNAME = (os.getenv("BOT_USERNAME") or "InstaGroqai_bot").strip()

# ✅ админ (твой user_id) + секрет для команд в группе
ADMIN_USER_ID = int((os.getenv("ADMIN_USER_ID") or "0").strip())
ADMIN_TOKEN = (os.getenv("ADMIN_TOKEN") or "").strip()

# ✅ файл доступа (простое хранение; на Railway может сбрасываться при redeploy)
ACCESS_FILE = "access.json"


def is_valid_https_url(url: str) -> bool:
    return url.startswith("https://") and len(url) > len("https://")


def send_log_http(text: str):
    if not BOT_TOKEN:
        print("LOG ERROR: BOT_TOKEN empty")
        return
    if not LOG_GROUP_ID:
        print("LOG ERROR: LOG_GROUP_ID empty/0")
        return

    try:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": LOG_GROUP_ID, "text": text},
            timeout=12,
        )
        if not r.ok:
            print("LOG ERROR:", r.status_code, r.text)
    except Exception as e:
        print("LOG ERROR: requests exception:", e)


def load_access() -> Dict[str, Any]:
    try:
        with open(ACCESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}


def save_access(data: Dict[str, Any]) -> None:
    try:
        with open(ACCESS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("ACCESS SAVE ERROR:", e)


def get_user_access(user_id: int) -> Dict[str, Any]:
    db = load_access()
    return db.get(str(user_id), {"paid": False, "free": False, "blocked": False})


def set_user_access(user_id: int, **kwargs):
    db = load_access()
    key = str(user_id)
    cur = db.get(key, {"paid": False, "free": False, "blocked": False})
    cur.update(kwargs)
    db[key] = cur
    save_access(db)
    return cur


def has_miniapp_access(user_id: int) -> bool:
    st = get_user_access(user_id)
    if st.get("blocked"):
        return False
    return bool(st.get("paid") or st.get("free"))


def main_menu_for(user_id: int) -> InlineKeyboardMarkup:
    keyboard = []

    # 🔐 доступ к miniapp
    if is_valid_https_url(MINIAPP_URL) and has_miniapp_access(user_id):
        keyboard.append([InlineKeyboardButton("🚀 Открыть Mini App", web_app=WebAppInfo(url=MINIAPP_URL))])
    else:
        # вместо webapp — callback, чтобы показать “нужно купить”
        keyboard.append([InlineKeyboardButton("🚀 Открыть Mini App", callback_data="need_pay")])

    keyboard.append([InlineKeyboardButton("⭐ Купить пакет", callback_data="buy_pack")])
    keyboard.append([
        InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
        InlineKeyboardButton("❓ Помощь", callback_data="help"),
    ])

    return InlineKeyboardMarkup(keyboard)


def build_start_log(update: Update) -> str:
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    username = (user.username or "—") if user else "—"
    full_name = f"{(user.first_name or '') if user else ''} {(user.last_name or '') if user else ''}".strip() or "—"

    chat_type = chat.type if chat else "—"
    chat_id = chat.id if chat else "—"
    text = (msg.text or "").strip() if msg else ""

    return (
        "🚀 /start\n"
        f"🕒 {time_str}\n"
        f"👤 {full_name} (@{username})\n"
        f"🆔 user_id: {user.id if user else '—'}\n"
        f"💬 chat_type: {chat_type}\n"
        f"🏷 chat_id: {chat_id}\n"
        f"✉️ text: {text}"
    )


def is_admin(update: Update) -> bool:
    user = update.effective_user
    if not user:
        return False
    return ADMIN_USER_ID != 0 and user.id == ADMIN_USER_ID


def is_from_log_group(update: Update) -> bool:
    chat = update.effective_chat
    return bool(chat and LOG_GROUP_ID and chat.id == LOG_GROUP_ID)


def parse_admin_cmd(text: str):
    # формат: /free <id> <token>
    parts = (text or "").strip().split()
    if not parts:
        return None, None, None
    cmd = parts[0].lstrip("/").lower()
    user_id = None
    token = None
    if len(parts) >= 2:
        try:
            user_id = int(parts[1])
        except Exception:
            user_id = None
    if len(parts) >= 3:
        token = parts[2]
    return cmd, user_id, token


# ---------- HANDLERS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # лог /start
    send_log_http(build_start_log(update))

    # меню
    user = update.effective_user
    uid = user.id if user else 0
    if update.effective_message:
        await update.effective_message.reply_text(
            "🤖 InstaGroq AI\n\nВыбирай действие кнопками ниже 👇",
            reply_markup=main_menu_for(uid),
        )


# ✅ на случай групп: /start или /start@BotUserName
async def start_from_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    user = query.from_user
    uid = user.id if user else 0

    if data == "need_pay":
        await query.message.reply_text("⛔ Доступ закрыт. Сначала купи пакет: нажми кнопку «⭐ Купить пакет».")
        return

    if data == "buy_pack":
        await query.message.reply_text(
            "⭐ Пакеты сообщений (пример):\n"
            "• 100 сообщений — 99₽\n"
            "• 500 сообщений — 399₽\n"
            "• 2000 сообщений — 999₽\n\n"
            "Оплату подключим позже.\n"
            "Пока доступ выдаётся вручную админом."
        )
        return

    if data == "settings":
        await query.message.reply_text("⚙️ Настройки скоро появятся.")
        return

    if data == "help":
        await query.message.reply_text("❓ Нажми «Открыть Mini App» и пиши в чат внутри Mini App.")
        return

    # если надо “обновить меню” (не обязательно)
    if data == "refresh":
        await query.message.reply_text("Меню обновлено ✅", reply_markup=main_menu_for(uid))
        return


# ---------- ADMIN (только в лог-группе) ----------
async def admin_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not msg.text:
        return

    # 1) только из LOG_GROUP_ID
    if not is_from_log_group(update):
        return

    # 2) только от админа
    if not is_admin(update):
        return

    cmd, user_id, token = parse_admin_cmd(msg.text)
    if not cmd:
        return

    # 3) токен обязателен (чтобы никто не баловался)
    if ADMIN_TOKEN and token != ADMIN_TOKEN:
        await msg.reply_text("⛔ Неверный ADMIN_TOKEN.")
        return

    if cmd == "whoami":
        u = update.effective_user
        await msg.reply_text(f"🆔 твой user_id: {u.id}\n👤 @{u.username or '—'}")
        return

    if cmd in ("free", "paid", "block", "unblock", "status") and not user_id:
        await msg.reply_text("⚠️ Нужен user_id. Пример: /free 123456 TOKEN")
        return

    if cmd == "free":
        st = set_user_access(user_id, free=True, blocked=False)
        await msg.reply_text(f"✅ FREE выдан: {user_id}\n{st}")
        return

    if cmd == "paid":
        st = set_user_access(user_id, paid=True, blocked=False)
        await msg.reply_text(f"✅ PAID выдан: {user_id}\n{st}")
        return

    if cmd == "block":
        st = set_user_access(user_id, blocked=True)
        await msg.reply_text(f"⛔ Заблокирован: {user_id}\n{st}")
        return

    if cmd == "unblock":
        st = set_user_access(user_id, blocked=False)
        await msg.reply_text(f"✅ Разблокирован: {user_id}\n{st}")
        return

    if cmd == "status":
        st = get_user_access(user_id)
        await msg.reply_text(f"ℹ️ Статус {user_id}: {st}")
        return


# ---------- START BOT ----------
def start_bot():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # групповой вариант /start@BotUserName
    start_pattern = rf"^/start(@{BOT_USERNAME})?(\s|$)"
    app.add_handler(MessageHandler(filters.Regex(start_pattern), start_from_text))

    app.add_handler(CallbackQueryHandler(on_button))

    # админ-команды только из лог-группы (и только от ADMIN_USER_ID)
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^/(free|paid|block|unblock|status|whoami)\b"), admin_router))

    print("🤖 Telegram bot started")
    app.run_polling(stop_signals=None, close_loop=False)