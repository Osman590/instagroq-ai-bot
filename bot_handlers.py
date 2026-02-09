# bot_handlers.py
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


# =========================
#   UI: MENU + TABS
# =========================
MENU_TEXT = "🤖 InstaGroq AI\n\nВыбирай действие кнопками ниже 👇"

TAB_TEXT = {
    "blocked": "⛔ Доступ заблокирован.\n\nЕсли ты считаешь это ошибкой — напиши админу.",
    "need_pay": "⭐ Чтобы открыть Mini App, нужно купить пакет.\n\nОплату подключим позже.",
    "buy_pack": (
        "⭐ Купить пакет\n\n"
        "Пакеты сообщений (пример):\n"
        "• 100 сообщений — 99₽\n"
        "• 500 сообщений — 399₽\n"
        "• 2000 сообщений — 999₽\n\n"
        "Оплату подключим позже."
    ),
    "settings": "⚙️ Настройки\n\nСкоро добавим настройки в боте.",
    "help": "❓ Помощь\n\nНажми «Открыть Mini App».",
    # дополнительные вкладки-заглушки
    "profile": "👤 Профиль\n\nРаздел в разработке.",
    "status": "📌 Статус\n\nРаздел в разработке.",
    "ref": "🎁 Рефералы\n\nРаздел в разработке.",
    "support": "💬 Поддержка\n\nРаздел в разработке.",
    "faq": "📚 FAQ\n\nРаздел в разработке.",
    "about": "ℹ️ О проекте\n\nРаздел в разработке.",
}


def tab_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")]])


def main_menu_for_user(user_id: int) -> InlineKeyboardMarkup:
    a = get_access(user_id) if user_id else {"is_free": False, "is_blocked": False}

    keyboard = []

    # если заблокирован — показываем вкладку "blocked" (по нажатию откроется вкладка)
    if a.get("is_blocked"):
        keyboard.append([InlineKeyboardButton("⛔ Доступ заблокирован", callback_data="tab:blocked")])
        return InlineKeyboardMarkup(keyboard)

    # открыть miniapp: если free -> web_app, иначе вкладка оплаты
    if a.get("is_free") and is_valid_https_url(MINIAPP_URL):
        keyboard.append([InlineKeyboardButton("🚀 Открыть Mini App", web_app=WebAppInfo(url=MINIAPP_URL))])
    else:
        keyboard.append([InlineKeyboardButton("🚀 Открыть Mini App", callback_data="tab:need_pay")])

    # основные вкладки
    keyboard.append([InlineKeyboardButton("⭐ Купить пакет", callback_data="tab:buy_pack")])
    keyboard.append([
        InlineKeyboardButton("⚙️ Настройки", callback_data="tab:settings"),
        InlineKeyboardButton("❓ Помощь", callback_data="tab:help"),
    ])

    # дополнительные вкладки (заглушки)
    keyboard.append([
        InlineKeyboardButton("👤 Профиль", callback_data="tab:profile"),
        InlineKeyboardButton("📌 Статус", callback_data="tab:status"),
    ])
    keyboard.append([
        InlineKeyboardButton("🎁 Рефералы", callback_data="tab:ref"),
        InlineKeyboardButton("💬 Поддержка", callback_data="tab:support"),
    ])
    keyboard.append([
        InlineKeyboardButton("📚 FAQ", callback_data="tab:faq"),
        InlineKeyboardButton("ℹ️ О проекте", callback_data="tab:about"),
    ])

    return InlineKeyboardMarkup(keyboard)


# =========================
#   MENU MESSAGE MANAGEMENT
# =========================
async def delete_prev_menu(bot, user_id: int):
    chat_id, msg_id = get_last_menu(user_id)
    if not chat_id or not msg_id:
        return
    try:
        await bot.delete_message(chat_id=chat_id, message_id=msg_id)
    except Exception:
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


async def edit_to_menu(context: ContextTypes.DEFAULT_TYPE, query, user_id: int):
    try:
        await query.message.edit_text(MENU_TEXT, reply_markup=main_menu_for_user(user_id))
        set_last_menu(user_id, user_id, query.message.message_id)
    except Exception:
        await send_fresh_menu(context.bot, user_id, MENU_TEXT)


async def edit_to_tab(context: ContextTypes.DEFAULT_TYPE, query, user_id: int, tab_key: str):
    text = TAB_TEXT.get(tab_key, "Раздел в разработке.")
    try:
        await query.message.edit_text(text, reply_markup=tab_kb())
        set_last_menu(user_id, user_id, query.message.message_id)
    except Exception:
        await send_fresh_menu(context.bot, user_id, MENU_TEXT)


# =========================
#   HANDLERS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    send_log_http(build_start_log(update))

    user = update.effective_user
    uid = user.id if user else 0
    if not uid:
        return

    await send_fresh_menu(context.bot, uid, MENU_TEXT)


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = (query.data or "").strip()

    # обязательно отвечаем на callback, но НЕ шлём сообщений
    try:
        await query.answer()
    except Exception:
        pass

    user = update.effective_user
    uid = user.id if user else 0
    if not uid:
        return

    # назад в меню
    if data == "back_to_menu":
        await edit_to_menu(context, query, uid)
        return

    # вкладки: tab:<key>
    if data.startswith("tab:"):
        key = data.split("tab:", 1)[1].strip()
        await edit_to_tab(context, query, uid, key)
        return

    # если пришло что-то неизвестное — просто вернём меню
    await edit_to_menu(context, query, uid)