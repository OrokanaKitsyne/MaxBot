
from flask import Flask, request, jsonify
import requests
from bot_logic import BotLogic

TOKEN = "f9LHodD0cOJSnxryoojbcFL5F8ynl9gd27z9_YVCGNC845alHzhM-_DebfOWrQkL1-3NDwdj-DWCG6UxgaeJ"
BASE_URL = "https://platform-api.max.ru"

app = Flask(__name__)
bot = BotLogic()


def get_start_button():
    return [
        {
            "type": "inline_keyboard",
            "payload": {
                "buttons": [
                    [
                        {
                            "type": "message",
                            "text": "Начать разговор",
                            "message": "/start"
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

    if data.get("update_type") == "message_created":
        message = data.get("message", {})
        chat_id = message.get("recipient", {}).get("chat_id")
        text = (message.get("body", {}).get("text") or "").strip()

        print("CHAT ID:", chat_id, flush=True)
        print("TEXT:", text, flush=True)

        if chat_id:
            response_text = bot.get_response(text)

            if text == "/start":
                send_message(chat_id, response_text, attachments=get_start_button())
            else:
                send_message(chat_id, response_text)

    return jsonify({"status": "ok"}), 200
