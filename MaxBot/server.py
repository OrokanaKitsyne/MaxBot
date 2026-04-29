import os
from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from reminder_scheduler import ReminderScheduler
from bot_logic import BotLogic
from feedback_logic import FeedbackBotLogic
from reminder_logic import ReminderBotLogic
from max_api import send_message


MAIN_TOKEN = os.getenv("MAX_BOT_TOKEN", "").strip()
FEEDBACK_TOKEN = os.getenv("MAX_FEEDBACK_BOT_TOKEN", "").strip()
REMINDER_TOKEN = os.getenv("MAX_REMINDER_BOT_TOKEN", "").strip()

if not MAIN_TOKEN:
    raise ValueError("Не задана переменная окружения MAX_BOT_TOKEN")

if not FEEDBACK_TOKEN:
    raise ValueError("Не задана переменная окружения MAX_FEEDBACK_BOT_TOKEN")

if not REMINDER_TOKEN:
    raise ValueError("Не задана переменная окружения MAX_REMINDER_BOT_TOKEN")


app = Flask(__name__)

main_bot = BotLogic()
feedback_bot = FeedbackBotLogic()
reminder_bot = ReminderBotLogic()


@app.route("/health")
def health():
    return "OK", 200


@app.route("/")
def home():
    return "Bot is running", 200


@app.route("/webhook", methods=["POST"])
def main_webhook():
    data = request.get_json(silent=True) or {}
    print("MAIN UPDATE:", data, flush=True)

    try:
        update_type = data.get("update_type")

        if update_type == "bot_started":
            chat_id = data.get("chat_id")
            if chat_id:
                text = main_bot.get_response("/start", user_id=str(chat_id))
                send_message(MAIN_TOKEN, chat_id, text)

        elif update_type == "message_created":
            message = data.get("message", {})
            chat_id = message.get("recipient", {}).get("chat_id")
            user_id = message.get("sender", {}).get("user_id")
            text = (message.get("body", {}).get("text") or "").strip()

            if chat_id and user_id:
                answer = main_bot.get_response(text, user_id=str(user_id))
                send_message(MAIN_TOKEN, chat_id, answer)

    except Exception as e:
        print("MAIN WEBHOOK ERROR:", str(e), flush=True)

    return jsonify({"status": "ok"}), 200


@app.route("/webhook/feedback", methods=["POST"])
def feedback_webhook():
    data = request.get_json(silent=True) or {}
    print("FEEDBACK UPDATE:", data, flush=True)

    # сюда можно потом вынести feedback по такому же принципу
    return jsonify({"status": "ok"}), 200


@app.route("/webhook/reminder", methods=["POST"])
def reminder_webhook():
    data = request.get_json(silent=True) or {}
    print("REMINDER UPDATE:", data, flush=True)

    try:
        response = reminder_bot.handle_update(data)

        if response:
            send_message(
                REMINDER_TOKEN,
                response["chat_id"],
                response["text"],
                attachments=response.get("attachments")
            )

    except Exception as e:
        print("REMINDER WEBHOOK ERROR:", str(e), flush=True)

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
