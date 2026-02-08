import os
import sqlite3
from datetime import datetime, timezone

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

# ✅ Группа, где ты админишь (и куда уже приходят логи)
TARGET_GROUP_ID = int(os.getenv("TARGET_GROUP_ID") or "-4697406654")

# ✅ Твои админ-данные
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID") or "0")
ADMIN_TOKEN = (os.getenv("ADMIN_TOKEN") or "").strip()

# ✅ общая БД для доступа (лежит рядом с кодом)
DB_PATH = os.getenv("ACCESS_DB_PATH") or "access.db"


def _now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_access(
          user_id INTEGER PRIMARY KEY,
          free_until INTEGER,
          blocked_until INTEGER,
          updated_at INTEGER
        )
        """
    )
    conn.commit()
    return conn


def _is_admin(update: Update) -> bool:
    msg = update.effective_message
    user = update.effective_user
    if not msg or not user:
        return False

    # админ-команды принимаем ТОЛЬКО из нужной группы
    if msg.chat_id != TARGET_GROUP_ID:
        return False

    # если sender = ты — ок
    if ADMIN_USER_ID and user.id == ADMIN_USER_ID:
        return True

    # иначе можно через секрет в тексте
    if ADMIN_TOKEN and (msg.text or "").find(ADMIN_TOKEN) != -1:
        return True

    return False


def is_valid_https_url(url: str) -> bool:
    return url.startswith("https://") and len(url) > len("https://")


# ---------- KEYBOARDS ----------
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
            InlineKeyboardButton(
                "🚀 Mini App (URL не настроен)",
                callback_data="miniapp_not_set",
            )
        ])

    keyboard.append([
        InlineKeyboardButton("⭐ Купить пакет", callback_data="buy_pack"),
    ])

    keyboard.append([
        InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
        InlineKeyboardButton("❓ Помощь", callback_data="help"),
    ])

    return InlineKeyboardMarkup(keyboard)


# ---------- HANDLERS ----------
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
            "⚠️ MINIAPP_URL не настроен.\n\n"
            "Добавь в Railway → Variables:\n"
            "MINIAPP_URL = https://<твой-github-pages>"
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
        await query.message.reply_text("❓ Нажми «Открыть Mini App» и пиши в чат внутри Mini App.")
        return


# ---------- ADMIN COMMANDS (в группе) ----------
async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        return
    await update.effective_message.reply_text(
        "🛠 Админ команды (пиши в ЭТОЙ группе):\n\n"
        "1) /free <user_id> [days]\n"
        "   пример: /free 123456789 30\n"
        "   (если days не указать — бесплатно навсегда)\n\n"
        "2) /block <user_id> [minutes]\n"
        "   пример: /block 123456789 60\n"
        "   (если minutes не указать — блок навсегда)\n\n"
        "3) /unblock <user_id>\n"
        "4) /status <user_id>\n"
        "5) /whoami  (покажет твой user_id)\n"
    )


async def whoami(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    if not msg or not user:
        return
    await msg.reply_text(f"👤 your user_id: {user.id}")


def _set_free(user_id: int, days: int | None):
    now = _now_ts()
    free_until = -1 if days is None else (now + int(days) * 86400)

    with _db() as conn:
        conn.execute(
            """
            INSERT INTO user_access(user_id, free_until, blocked_until, updated_at)
            VALUES(?, ?, COALESCE((SELECT blocked_until FROM user_access WHERE user_id=?), NULL), ?)
            ON CONFLICT(user_id) DO UPDATE SET
              free_until=excluded.free_until,
              updated_at=excluded.updated_at
            """,
            (user_id, free_until, user_id, now),
        )
        conn.commit()


def _set_block(user_id: int, minutes: int | None):
    now = _now_ts()
    blocked_until = -1 if minutes is None else (now + int(minutes) * 60)

    with _db() as conn:
        conn.execute(
            """
            INSERT INTO user_access(user_id, free_until, blocked_until, updated_at)
            VALUES(?, COALESCE((SELECT free_until FROM user_access WHERE user_id=?), NULL), ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
              blocked_until=excluded.blocked_until,
              updated_at=excluded.updated_at
            """,
            (user_id, user_id, blocked_until, now),
        )
        conn.commit()


def _unset_block(user_id: int):
    now = _now_ts()
    with _db() as conn:
        conn.execute(
            """
            INSERT INTO user_access(user_id, free_until, blocked_until, updated_at)
            VALUES(?, COALESCE((SELECT free_until FROM user_access WHERE user_id=?), NULL), NULL, ?)
            ON CONFLICT(user_id) DO UPDATE SET
              blocked_until=NULL,
              updated_at=excluded.updated_at
            """,
            (user_id, user_id, now),
        )
        conn.commit()


def _get_status(user_id: int) -> str:
    now = _now_ts()
    with _db() as conn:
        row = conn.execute(
            "SELECT free_until, blocked_until, updated_at FROM user_access WHERE user_id=?",
            (user_id,),
        ).fetchone()

    if not row:
        return "нет записи (по умолчанию: платно)"

    free_until, blocked_until, updated_at = row

    def fmt(ts: int | None):
        if ts is None:
            return "—"
        if ts == -1:
            return "навсегда"
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    is_free = (free_until == -1) or (isinstance(free_until, int) and free_until > now)
    is_blocked = (blocked_until == -1) or (isinstance(blocked_until, int) and blocked_until > now)

    return (
        f"user_id: {user_id}\n"
        f"FREE: {'✅' if is_free else '❌'} (until: {fmt(free_until)})\n"
        f"BLOCKED: {'✅' if is_blocked else '❌'} (until: {fmt(blocked_until)})\n"
        f"updated_at: {fmt(updated_at)}"
    )


async def cmd_free(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        return

    args = context.args or []
    if not args:
        await update.effective_message.reply_text("Формат: /free <user_id> [days]")
        return

    user_id = int(args[0])
    days = int(args[1]) if len(args) >= 2 else None

    _set_free(user_id, days)
    await update.effective_message.reply_text(f"✅ FREE установлен для {user_id}")


async def cmd_block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        return

    args = context.args or []
    if not args:
        await update.effective_message.reply_text("Формат: /block <user_id> [minutes]")
        return

    user_id = int(args[0])
    minutes = int(args[1]) if len(args) >= 2 else None

    _set_block(user_id, minutes)
    await update.effective_message.reply_text(f"⛔ BLOCK установлен для {user_id}")


async def cmd_unblock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        return

    args = context.args or []
    if not args:
        await update.effective_message.reply_text("Формат: /unblock <user_id>")
        return

    user_id = int(args[0])
    _unset_block(user_id)
    await update.effective_message.reply_text(f"✅ UNBLOCK для {user_id}")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        return

    args = context.args or []
    if not args:
        await update.effective_message.reply_text("Формат: /status <user_id>")
        return

    user_id = int(args[0])
    await update.effective_message.reply_text("ℹ️ " + _get_status(user_id))


# ---------- START BOT ----------
def start_bot():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_button))

    # админ-команды
    app.add_handler(CommandHandler("admin", admin_help))
    app.add_handler(CommandHandler("whoami", whoami))
    app.add_handler(CommandHandler("free", cmd_free))
    app.add_handler(CommandHandler("block", cmd_block))
    app.add_handler(CommandHandler("unblock", cmd_unblock))
    app.add_handler(CommandHandler("status", cmd_status))

    print("🤖 Telegram bot started")
    app.run_polling(stop_signals=None, close_loop=False)