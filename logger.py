import os
from telegram import Bot
from telegram.constants import ParseMode

BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()

# ID группы или канала для логов
# ❗️ОБЯЗАТЕЛЬНО отрицательное число для группы
LOG_CHAT_ID = int(os.getenv("LOG_CHAT_ID") or "0")

bot = Bot(token=BOT_TOKEN)


def log_event(text: str):
    if not BOT_TOKEN or not LOG_CHAT_ID:
        return
    try:
        bot.send_message(
            chat_id=LOG_CHAT_ID,
            text=text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    except Exception as e:
        print("LOG ERROR:", e)


def log_chat(
    user_id: int,
    username: str | None,
    user_text: str,
    ai_reply: str,
):
    uname = f"@{username}" if username else "—"

    msg = (
        "🧠 <b>AI Chat</b>\n\n"
        f"👤 <b>User:</b> {uname}\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n\n"
        f"💬 <b>Запрос:</b>\n"
        f"<blockquote>{user_text}</blockquote>\n\n"
        f"🤖 <b>Ответ ИИ:</b>\n"
        f"<blockquote>{ai_reply}</blockquote>"
    )

    log_event(msg)