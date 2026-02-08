# bot_admin.py
import os
import re
from telegram import Update
from telegram.ext import ContextTypes

from api import set_free, set_blocked, get_access
from bot_menu import main_menu

MINIAPP_URL = (os.getenv("MINIAPP_URL") or "").strip()

ADMIN_USER_ID_RAW = (os.getenv("ADMIN_USER_ID") or "0").strip()
try:
    ADMIN_USER_ID = int(ADMIN_USER_ID_RAW)
except Exception:
    ADMIN_USER_ID = 0

# где разрешены админ-команды (в группе логов)
GROUP_ID_RAW = (os.getenv("TARGET_GROUP_ID") or os.getenv("LOG_GROUP_ID") or "0").strip()
try:
    ADMIN_GROUP_ID = int(GROUP_ID_RAW)
except Exception:
    ADMIN_GROUP_ID = 0


def is_admin(update: Update) -> bool:
    u = update.effective_user
    c = update.effective_chat
    if not u or not c:
        return False
    if ADMIN_USER_ID and u.id != ADMIN_USER_ID:
        return False
    if ADMIN_GROUP_ID and c.id != ADMIN_GROUP_ID:
        return False
    return True


def parse_user_id(arg: str) -> int:
    s = (arg or "").strip()
    s = re.sub(r"[^\d\-]", "", s)
    try:
        return int(s)
    except Exception:
        return 0


def _access_dict(uid: int) -> dict:
    a = get_access(uid)
    return a if isinstance(a, dict) else {}


async def push_user_menu(context: ContextTypes.DEFAULT_TYPE, uid: int):
    """
    Сразу отправляет пользователю обновлённое меню.
    """
    a = _access_dict(uid)

    if a.get("blocked"):
        text = "⛔ Доступ ограничен. Обратись к администратору."
    elif a.get("free") or a.get("paid"):
        text = "✅ Доступ активен. Нажми кнопку ниже 👇"
    else:
        text = "⭐ Чтобы открыть Mini App — купи пакет (или админ выдаст FREE)."

    await context.bot.send_message(
        chat_id=uid,
        text=text,
        reply_markup=main_menu(MINIAPP_URL, a),
    )


async def cmd_whoami(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    u = update.effective_user
    await update.effective_message.reply_text(f"✅ ты админ\nuser_id: {u.id}")


async def cmd_free(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    if not context.args:
        await update.effective_message.reply_text("Использование: /free <user_id>")
        return

    uid = parse_user_id(context.args[0])
    if not uid:
        await update.effective_message.reply_text("❌ Не вижу user_id. Нужно число.")
        return

    set_free(uid, True)
    a = _access_dict(uid)

    await update.effective_message.reply_text(f"✅ FREE включен для {uid}\n{a}")

    # ✅ ВАЖНО: обновляем меню пользователю сразу
    try:
        await push_user_menu(context, uid)
    except Exception as e:
        await update.effective_message.reply_text(f"⚠️ Не смог отправить меню пользователю: {e}")


async def cmd_paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    if not context.args:
        await update.effective_message.reply_text("Использование: /paid <user_id>")
        return

    uid = parse_user_id(context.args[0])
    if not uid:
        await update.effective_message.reply_text("❌ Не вижу user_id. Нужно число.")
        return

    # paid = free выключаем (у тебя пока так)
    set_free(uid, False)
    a = _access_dict(uid)

    await update.effective_message.reply_text(f"✅ FREE отключен (теперь платно) для {uid}\n{a}")

    # ✅ Обновляем меню пользователю сразу
    try:
        await push_user_menu(context, uid)
    except Exception as e:
        await update.effective_message.reply_text(f"⚠️ Не смог отправить меню пользователю: {e}")


async def cmd_block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    if not context.args:
        await update.effective_message.reply_text("Использование: /block <user_id>")
        return

    uid = parse_user_id(context.args[0])
    if not uid:
        await update.effective_message.reply_text("❌ Не вижу user_id. Нужно число.")
        return

    set_blocked(uid, True)
    a = _access_dict(uid)

    await update.effective_message.reply_text(f"⛔ Заблокирован {uid}\n{a}")

    # ✅ Сразу отправляем новое меню (без кнопки миниаппа)
    try:
        await push_user_menu(context, uid)
    except Exception as e:
        await update.effective_message.reply_text(f"⚠️ Не смог отправить меню пользователю: {e}")


async def cmd_unblock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    if not context.args:
        await update.effective_message.reply_text("Использование: /unblock <user_id>")
        return

    uid = parse_user_id(context.args[0])
    if not uid:
        await update.effective_message.reply_text("❌ Не вижу user_id. Нужно число.")
        return

    set_blocked(uid, False)
    a = _access_dict(uid)

    await update.effective_message.reply_text(f"✅ Разблокирован {uid}\n{a}")

    # ✅ Обновляем меню сразу
    try:
        await push_user_menu(context, uid)
    except Exception as e:
        await update.effective_message.reply_text(f"⚠️ Не смог отправить меню пользователю: {e}")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    if not context.args:
        await update.effective_message.reply_text("Использование: /status <user_id>")
        return

    uid = parse_user_id(context.args[0])
    if not uid:
        await update.effective_message.reply_text("❌ Не вижу user_id. Нужно число.")
        return

    a = get_access(uid)
    await update.effective_message.reply_text(f"ℹ️ Статус {uid}\n{a}")