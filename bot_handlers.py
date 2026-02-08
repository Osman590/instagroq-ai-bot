import os
from datetime import datetime

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes

from api import get_access

BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()
MINIAPP_URL = (os.getenv("MINIAPP_URL") or "").strip()

# лог-группа: TARGET_GROUP_ID приоритет
GROUP_ID_RAW = (os.getenv("TARGET_GROUP_ID") or os.getenv("LOG_GROUP_ID") or "0").strip()
try:
    GROUP_ID = int(GROUP_ID_RAW)
except Exception:
    GROUP_ID = 0


def is_valid_https_url(url: str) -> bool:
    return url.startswith("https://") and len(url) > len("https://")


def send_log_http(text: str):
    if not BOT_TOKEN or not GROUP_ID:
        return
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": GROUP_ID, "text": text},
            timeout=12,
        )
        if not r.ok:
            print("LOG ERROR:", r.status_code, r.text)
    except Exception as e:
        print("LOG ERROR:", e)


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


def normalize_access(a: dict | None) -> dict:
    """
    Приводим к единому виду:
      free: bool
      paid: bool
      blocked: bool
    Поддерживаем и старые ключи is_free/is_blocked
    """
    a = a if isinstance(a, dict) else {}
    free = bool(a.get("free") or a.get("is_free"))
    paid = bool(a.get("paid") or a.get("is_paid"))
    blocked = bool(a.get("blocked") or a.get("is_blocked"))
    return {"free": free, "paid": paid, "blocked": blocked}


def main_menu_for_user(user_id: int) -> InlineKeyboardMarkup:
    a_raw = get_access(user_id) if user_id else {}
    a = normalize_access(a_raw)

    keyboard = []

    # 1) URL не настроен
    if not is_valid_https_url(MINIAPP_URL):
        keyboard.append([InlineKeyboardButton("🚀 Mini App (URL не настроен)", callback_data="miniapp_not_set")])
        keyboard.append([InlineKeyboardButton("⭐ Купить пакет", callback_data="buy_pack")])
        keyboard.append([
            InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
            InlineKeyboardButton("❓ Помощь", callback_data="help"),
        ])
        return InlineKeyboardMarkup(keyboard)

    # 2) Заблокирован
    if a["blocked"]:
        keyboard.append([InlineKeyboardButton("⛔ Доступ заблокирован", callback_data="blocked")])
        keyboard.append([InlineKeyboardButton("❓ Помощь", callback_data="help")])
        return InlineKeyboardMarkup(keyboard)

    # 3) Доступ есть (FREE или PAID) → открываем miniapp
    can_open = a["free"] or a["paid"]
    if can_open:
        keyboard.append([InlineKeyboardButton("🚀 Открыть Mini App", web_app=WebAppInfo(url=MINIAPP_URL))])
    else:
        keyboard.append([InlineKeyboardButton("🚀 Открыть Mini App", callback_data="need_pay")])

    keyboard.append([InlineKeyboardButton("⭐ Купить пакет", callback_data="buy_pack")])
    keyboard.append([
        InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
        InlineKeyboardButton("❓ Помощь", callback_data="help"),
    ])

    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    send_log_http(build_start_log(update))

    user = update.effective_user
    uid = user.id if user else 0

    await update.effective_message.reply_text(
        "🤖 InstaGroq AI\n\nВыбирай действие кнопками ниже 👇",
        reply_markup=main_menu_for_user(uid),
    )


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "miniapp_not_set":
        await query.message.reply_text(
            "⚠️ MINIAPP_URL не настроен.\n"
            "Добавь в Railway → Variables: MINIAPP_URL = https://..."
        )
        return

    if data == "blocked":
        await query.message.reply_text("⛔ Тебя заблокировали. Напиши администратору.")
        return

    if data == "need_pay":
        await query.message.reply_text(
            "⭐ Чтобы открыть Mini App, нужно купить пакет.\n"
            "Нажми «Купить пакет»."
        )
        return

    if data == "buy_pack":
        await query.message.reply_text(
            "⭐ Пакеты сообщений (пример):\n"
            "• 100 сообщений — 99₽\n"
            "• 500 сообщений — 399₽\n"
            "• 2000 сообщений — 999₽\n\n"
            "Оплату подключим позже."
        )
        return

    if data == "settings":
        await query.message.reply_text("⚙️ Настройки скоро появятся.")
        return

    if data == "help":
        await query.message.reply_text("❓ Если у тебя есть доступ — кнопка откроет Mini App.")
        return