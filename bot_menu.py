# bot_menu.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


def is_valid_https_url(url: str) -> bool:
    return url.startswith("https://") and len(url) > len("https://")


def main_menu(miniapp_url: str, access: dict | None = None) -> InlineKeyboardMarkup:
    """
    access ожидаем в виде dict, например:
      {"free": True/False, "paid": True/False, "blocked": True/False}
    Если access=None — ведём себя как раньше (показываем кнопку, если url ок).
    """
    access = access or {}
    is_blocked = bool(access.get("blocked"))
    is_free = bool(access.get("free"))
    is_paid = bool(access.get("paid"))
    can_open = (is_free or is_paid) and (not is_blocked)

    keyboard = []

    # --- MINI APP BUTTON ---
    if not is_valid_https_url(miniapp_url):
        keyboard.append([InlineKeyboardButton("🚀 Mini App (URL не настроен)", callback_data="miniapp_not_set")])
    else:
        if is_blocked:
            # бан — кнопку не показываем
            pass
        else:
            if can_open:
                keyboard.append([InlineKeyboardButton("🚀 Открыть Mini App", web_app=WebAppInfo(url=miniapp_url))])
            else:
                # нет доступа — вместо web_app делаем callback
                keyboard.append([InlineKeyboardButton("🚀 Открыть Mini App", callback_data="need_payment")])

    # --- BUY PACK ---
    keyboard.append([InlineKeyboardButton("⭐ Купить пакет", callback_data="buy_pack")])

    # --- OTHER ---
    keyboard.append([
        InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
        InlineKeyboardButton("❓ Помощь", callback_data="help"),
    ])

    return InlineKeyboardMarkup(keyboard)