import os
from flask import Flask, request, jsonify
import requests
from bot_logic import BotLogic

TOKEN = os.getenv("MAX_BOT_TOKEN", "").strip()
BASE_URL = "https://platform-api.max.ru"

if not TOKEN:
    raise ValueError("Не задана переменная окружения MAX_BOT_TOKEN")

app = Flask(__name__)
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
                    ]
                ]
            }
        }
    ]
    
def send_message(chat_id, text):
    url = f"{BASE_URL}/messages?chat_id={chat_id}"

    headers = {
        "Authorization": TOKEN,
        "Content-Type": "application/json"
    }

    payload = {
        "text": text
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
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

    update_type = data.get("update_type")

    if update_type == "bot_started":
        chat_id = data.get("chat_id")
        payload = data.get("payload")

        print("BOT STARTED CHAT ID:", chat_id, flush=True)
        print("BOT STARTED PAYLOAD:", payload, flush=True)

        if chat_id:
            send_message(
                chat_id,
                "Привет! Я бот-помощник по алгоритмике.\n\nНапиши тему или задачу, и я помогу."
            )

    elif update_type == "message_created":
        message = data.get("message", {})
        chat_id = message.get("recipient", {}).get("chat_id")
        text = (message.get("body", {}).get("text") or "").strip()

        print("CHAT ID:", chat_id, flush=True)
        print("TEXT:", text, flush=True)

        if chat_id:
            response_text = bot.get_response(text)
            send_message(chat_id, response_text)

    return jsonify({"status": "ok"}), 200
