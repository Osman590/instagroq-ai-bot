# bot_logging.py
import os
from datetime import datetime

import requests
from telegram import Update

# Эти переменные инициализируются через init_env()
BOT_TOKEN = ""
LOG_GROUP_ID = 0


def init_env():
    global BOT_TOKEN, LOG_GROUP_ID
    BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()
    LOG_GROUP_ID = int((os.getenv("LOG_GROUP_ID") or "0").strip() or "0")


def send_log_http(text: str):
    """
    Надёжная отправка в группу через Telegram HTTP API.
    Пишет ошибку в Railway Logs, если что-то не так.
    """
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