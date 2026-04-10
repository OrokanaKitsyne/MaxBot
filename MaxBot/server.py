from flask import Flask, request, jsonify
import requests
import os
from bot_logic import BotLogic

TOKEN = "f9LHodD0cOJSnxryoojbcFL5F8ynl9gd27z9_YVCGNC845alHzhM-_DebfOWrQkL1-3NDwdj-DWCG6UxgaeJ"
BASE_URL = "https://platform-api.max.ru"

app = Flask(__name__)
bot = BotLogic()

def send_message(chat_id, text):
    url = f"{BASE_URL}/messages"

    headers = {
        "Authorization": TOKEN,
        "Content-Type": "application/json"
    }

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        print("SEND STATUS:", response.status_code)
        print("SEND RESPONSE:", response.text)
    except Exception as e:
        print("SEND ERROR:", str(e))


@app.route("/")
def home():
    return "Bot is running", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}

    print("UPDATE:", data, flush=True)

    if data.get("update_type") == "message_created":
        message = data.get("message", {})
        chat_id = message.get("recipient", {}).get("chat_id")
        text = message.get("body", {}).get("text", "")

        print("CHAT ID:", chat_id, flush=True)
        print("TEXT:", text, flush=True)

        if chat_id:
            response = bot.get_response(text)
            send_message(chat_id, response)

    return jsonify({"status": "ok"}), 200
