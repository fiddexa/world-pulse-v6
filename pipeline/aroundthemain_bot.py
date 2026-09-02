import json
import os
import time
import urllib.parse
import urllib.request


BOT_TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
CHANNEL_USERNAME = "@aroundthemain"
CHANNEL_URL = "https://t.me/aroundthemain"


def telegram_request(method, data=None):
    url = f"https://api.telegram.org/bot{os.environ[BOT_TOKEN_ENV]}/{method}"

    encoded = urllib.parse.urlencode(data or {}).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=encoded,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def send_message(chat_id, text, reply_markup=None):
    data = {
        "chat_id": chat_id,
        "text": text,
    }

    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)

    return telegram_request("sendMessage", data)


def start_message():
    return (
        "🌍 AROUND THE MAIN\n\n"
        "News of the world that truly matter.\n\n"
        "We bring together significant events from "
        "around the world — geopolitics, economy, energy, "
        "technology, science, health, security and society.\n\n"
        "🔎 Independent sources.\n"
        "⚖️ Facts separated from analysis.\n"
        "📰 Three editions every day.\n\n"
        "Minimum text. Maximum meaning."
    )


def main():
    token = os.getenv(BOT_TOKEN_ENV)

    if not token:
        raise RuntimeError(
            f"{BOT_TOKEN_ENV} is not configured."
        )

    offset = None

    print("AROUND THE MAIN bot started.")

    while True:
        try:
            data = {
                "timeout": 30,
            }

            if offset is not None:
                data["offset"] = offset

            result = telegram_request("getUpdates", data)

            if not result.get("ok"):
                print("Telegram error:", result)
                time.sleep(5)
                continue

            for update in result.get("result", []):
                offset = update["update_id"] + 1

                message = update.get("message", {})
                chat = message.get("chat", {})
                text = message.get("text", "")

                if not chat:
                    continue

                chat_id = chat["id"]

                if text.startswith("/start"):
                    keyboard = {
                        "inline_keyboard": [
                            [
                                {
                                    "text": "📰 JOIN AROUND THE MAIN",
                                    "url": CHANNEL_URL,
                                }
                            ]
                        ]
                    }

                    send_message(
                        chat_id,
                        start_message(),
                        keyboard,
                    )

        except Exception as exc:
            print("Bot error:", repr(exc))
            time.sleep(5)


if __name__ == "__main__":
    main()
