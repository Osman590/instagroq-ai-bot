# bot_menu.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


def is_valid_https_url(url: str) -> bool:
    return url.startswith("https://") and len(url) > len("https://")


def main_menu(miniapp_url: str) -> InlineKeyboardMarkup:
    keyboard = []

    if is_valid_https_url(miniapp_url):
        keyboard.append([
            InlineKeyboardButton(
                "🚀 Открыть Mini App",
                web_app=WebAppInfo(url=miniapp_url),
            )
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(
                "🚀 Mini App (URL не настроен)",
                callback_data="miniapp_not_set",
            )
        ])

    keyboard.append([InlineKeyboardButton("⭐ Купить пакет", callback_data="buy_pack")])

    keyboard.append([
        InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
        InlineKeyboardButton("❓ Помощь", callback_data="help"),
    ])

    return InlineKeyboardMarkup(keyboard)