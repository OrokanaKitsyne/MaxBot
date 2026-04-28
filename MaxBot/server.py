import os
from flask import Flask, request, jsonify
import requests
from bot_logic import BotLogic

TOKEN = os.getenv("MAX_BOT_TOKEN", "").strip()
BASE_URL = "https://platform-api.max.ru"

if not TOKEN:
    raise ValueError("Не задана переменная окружения MAX_BOT_TOKEN")

app = Flask(__name__)
@app.route("/health")
def health():
    return "OK", 200
bot = BotLogic()


def get_main_keyboard():
    return [
        {
            "type": "inline_keyboard",
            "payload": {
                "buttons": [
                    [
                        {
                            "type": "message",
                            "text": "Список курсов",
                            "message": "список курсов"
                        },
                        {
                            "type": "message",
                            "text": "Контакты",
                            "message": "контакты"
                        }
                    ],
                    [
                        {
                            "type": "message",
                            "text": "Помощь",
                            "message": "помощь"
                        }
                    ],
                    [
                        {
                            "type": "message",
                            "text": "Записаться",
                            "message": "записаться"
                        }
                    ]
                ]
            }
        }
    ]


def send_message(chat_id, text, attachments=None):
    url = f"{BASE_URL}/messages?chat_id={chat_id}"

    headers = {
        "Authorization": TOKEN,
        "Content-Type": "application/json"
    }

    payload = {
        "text": text
    }

    if attachments:
        payload["attachments"] = attachments

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        print("SEND STATUS:", response.status_code, flush=True)
        print("SEND RESPONSE:", response.text, flush=True)
    except Exception as e:
        print("SEND ERROR:", str(e), flush=True)


@app.route("/", methods=["GET"])
def home():
    return "Bot is running", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}
    print("UPDATE:", data, flush=True)

    try:
        update_type = data.get("update_type")

        if update_type == "bot_started":
            chat_id = data.get("chat_id")

            print("BOT STARTED CHAT ID:", chat_id, flush=True)

            if chat_id:
                response_text = bot.get_response("/start", user_id=str(chat_id))
                send_message(chat_id, response_text, attachments=get_main_keyboard())

        elif update_type == "message_created":
            message = data.get("message", {})

            chat_id = message.get("recipient", {}).get("chat_id")
            user_id = message.get("sender", {}).get("user_id")
            text = (message.get("body", {}).get("text") or "").strip()

            print("CHAT ID:", chat_id, flush=True)
            print("USER ID:", user_id, flush=True)
            print("TEXT:", text, flush=True)

            if chat_id and user_id:
                response_text = bot.get_response(text, user_id=str(user_id))
                send_message(chat_id, response_text, attachments=get_main_keyboard())

    except Exception as e:
        print("WEBHOOK ERROR:", str(e), flush=True)

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
