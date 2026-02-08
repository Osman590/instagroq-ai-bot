import os
from datetime import datetime

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes

from api import get_access, get_last_menu, set_last_menu, clear_last_menu

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


def main_menu_for_user(user_id: int) -> InlineKeyboardMarkup:
    a = get_access(user_id) if user_id else {"is_free": False, "is_blocked": False}

    keyboard = []

    if a.get("is_blocked"):
        keyboard.append([InlineKeyboardButton("⛔ Доступ заблокирован", callback_data="blocked")])
        return InlineKeyboardMarkup(keyboard)

    # если FREE — настоящая кнопка открытия web_app
    if a.get("is_free") and is_valid_https_url(MINIAPP_URL):
        keyboard.append([InlineKeyboardButton("🚀 Открыть Mini App", web_app=WebAppInfo(url=MINIAPP_URL))])
    else:
        # иначе кнопка есть, но при нажатии просим купить пакет
        keyboard.append([InlineKeyboardButton("🚀 Открыть Mini App", callback_data="need_pay")])

    keyboard.append([InlineKeyboardButton("⭐ Купить пакет", callback_data="buy_pack")])
    keyboard.append([
        InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
        InlineKeyboardButton("❓ Помощь", callback_data="help"),
    ])
    return InlineKeyboardMarkup(keyboard)


async def delete_prev_menu(bot, user_id: int):
    chat_id, msg_id = get_last_menu(user_id)
    if not chat_id or not msg_id:
        return
    try:
        await bot.delete_message(chat_id=chat_id, message_id=msg_id)
    except Exception:
        # если уже удалено/нельзя — просто чистим запись
        pass
    clear_last_menu(user_id)


async def send_fresh_menu(bot, user_id: int, text: str):
    # удаляем предыдущее меню
    await delete_prev_menu(bot, user_id)

    # отправляем новое
    m = await bot.send_message(
        chat_id=user_id,
        text=text,
        reply_markup=main_menu_for_user(user_id),
    )
    set_last_menu(user_id, user_id, m.message_id)


async def send_block_notice(bot, user_id: int):
    # удаляем меню
    await delete_prev_menu(bot, user_id)

    # просто текст (без меню)
    await bot.send_message(chat_id=user_id, text="⛔ Доступ заблокирован.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    send_log_http(build_start_log(update))

    user = update.effective_user
    uid = user.id if user else 0
    if not uid:
        return

    # вместо reply_text → делаем “одно меню”
    await send_fresh_menu(
        context.bot,
        uid,
        "🤖 InstaGroq AI\n\nВыбирай действие кнопками ниже 👇",
    )


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "blocked":
        await query.message.reply_text("⛔ Тебя заблокировали.")
        return

    if data == "need_pay":
        await query.message.reply_text("⭐ Чтобы открыть Mini App, нужно купить пакет.")
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
        await query.message.reply_text("❓ Нажми «Открыть Mini App».")
        return