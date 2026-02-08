import os
import threading

from api import api
from bot import start_bot

# Railway / ENV
PORT = int(os.getenv("PORT", "8000"))


def run_api():
    api.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        use_reloader=False,
    )


def main():
    # Flask API — в отдельном потоке
    t = threading.Thread(target=run_api, daemon=True)
    t.start()

    # Telegram bot — основной поток
    start_bot()


if __name__ == "__main__":
    main()