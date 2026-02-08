import os
import re
from telegram import Update
from telegram.ext import ContextTypes

from api import set_free, set_blocked, get_access

ADMIN_USER_ID_RAW = (os.getenv("ADMIN_USER_ID") or "0").strip()
try:
    ADMIN_USER_ID = int(ADMIN_USER_ID_RAW)
except Exception:
    ADMIN_USER_ID = 0

ADMIN_TOKEN = (os.getenv("ADMIN_TOKEN") or "").strip()

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
    # 1) только ты
    if ADMIN_USER_ID and u.id != ADMIN_USER_ID:
        return False
    # 2) только в группе логов (как ты хотел)
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
    a = get_access(uid)
    await update.effective_message.reply_text(f"✅ FREE включен для {uid}\n{a}")


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
    set_free(uid, False)
    a = get_access(uid)
    await update.effective_message.reply_text(f"✅ FREE отключен (теперь платно) для {uid}\n{a}")


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
    a = get_access(uid)
    await update.effective_message.reply_text(f"⛔ Заблокирован {uid}\n{a}")


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
    a = get_access(uid)
    await update.effective_message.reply_text(f"✅ Разблокирован {uid}\n{a}")


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