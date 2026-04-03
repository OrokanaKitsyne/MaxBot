from flask import Flask, request, jsonify
import requests

TOKEN = "ТВОЙ_ТОКЕН"
BASE_URL = "https://platform-api.max.ru"

app = Flask(__name__)

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

    requests.post(url, headers=headers, json=payload)


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    print("ПРИШЁЛ UPDATE:")
    print(data)

    # 🔥 достаём данные
    if data.get("update_type") == "message_created":
        message = data.get("message", {})
        chat_id = message.get("chat_id")
        text = message.get("body", {}).get("text", "").lower()

        if chat_id:
            if text == "/start":
                send_message(chat_id, "Привет! Я бот 🚀")
            else:
                send_message(chat_id, f"Ты написал: {text}")

    return jsonify({"status": "ok"}), 200


@app.route("/")
def home():
    return "Bot is running", 200