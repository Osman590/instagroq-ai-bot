import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from bot_handlers import start, on_button
from bot_admin import (
    cmd_whoami,
    cmd_free,
    cmd_paid,
    cmd_block,
    cmd_unblock,
    cmd_status,
)

BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()


async def post_init(app: Application):
    # Команды для подсказок "/" (чтобы слева предлагались команды)
    # Покажутся у тех, кто пишет боту/в группе с ботом (Telegram сам решает где отображать)
    await app.bot.set_my_commands(
        [
            ("start", "Запуск меню"),
            ("whoami", "Проверка админа (в группе логов)"),
            ("free", "Сделать пользователя бесплатным: /free <user_id>"),
            ("paid", "Сделать пользователя платным: /paid <user_id>"),
            ("block", "Заблокировать: /block <user_id>"),
            ("unblock", "Разблокировать: /unblock <user_id>"),
            ("status", "Статус: /status <user_id>"),
        ]
    )


def start_bot():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # user
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_button))

    # admin (работают только в группе логов и только от ADMIN_USER_ID)
    app.add_handler(CommandHandler("whoami", cmd_whoami))
    app.add_handler(CommandHandler("free", cmd_free))
    app.add_handler(CommandHandler("paid", cmd_paid))
    app.add_handler(CommandHandler("block", cmd_block))
    app.add_handler(CommandHandler("unblock", cmd_unblock))
    app.add_handler(CommandHandler("status", cmd_status))

    print("🤖 Telegram bot started")
    app.run_polling(stop_signals=None, close_loop=False)