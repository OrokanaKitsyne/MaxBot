import os
from flask import Flask, request, jsonify
import requests

from bot_logic import BotLogic
from feedback_logic import FeedbackBotLogic


MAIN_TOKEN = os.getenv("MAX_BOT_TOKEN", "").strip()
FEEDBACK_TOKEN = os.getenv("MAX_FEEDBACK_BOT_TOKEN", "").strip()

BASE_URL = "https://platform-api.max.ru"

if not MAIN_TOKEN:
    raise ValueError("Не задана переменная окружения MAX_BOT_TOKEN")

if not FEEDBACK_TOKEN:
    raise ValueError("Не задана переменная окружения MAX_FEEDBACK_BOT_TOKEN")


app = Flask(__name__)

bot = BotLogic()
feedback_bot = FeedbackBotLogic()


@app.route("/health")
def health():
    return "OK", 200


@app.route("/", methods=["GET"])
def home():
    return "Bot is running", 200


def send_message(token, chat_id, text, attachments=None):
    url = f"{BASE_URL}/messages?chat_id={chat_id}"

    headers = {
        "Authorization": token,
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


def make_keyboard(buttons):
    return [
        {
            "type": "inline_keyboard",
            "payload": {
                "buttons": buttons
            }
        }
    ]


def get_main_keyboard():
    return make_keyboard([
        [
            {"type": "message", "text": "Список курсов", "message": "список курсов"},
            {"type": "message", "text": "Контакты", "message": "контакты"}
        ],
        [
            {"type": "message", "text": "Помощь", "message": "помощь"}
        ],
        [
            {"type": "message", "text": "Записаться", "message": "записаться"}
        ]
    ])


def get_feedback_start_keyboard():
    return make_keyboard([
        [
            {
                "type": "message",
                "text": "Список курсов",
                "message": "feedback:course_list"
            }
        ]
    ])


def get_courses_keyboard():
    buttons = []

    for course in feedback_bot.get_courses():
        buttons.append([
            {
                "type": "message",
                "text": course,
                "message": f"feedback:course:{course}"
            }
        ])

    return make_keyboard(buttons)


def get_lessons_keyboard(course_name):
    buttons = []

    for lesson_num in feedback_bot.get_lessons(course_name):
        buttons.append([
            {
                "type": "message",
                "text": f"Урок №{lesson_num}",
                "message": f"feedback:lesson:{lesson_num}"
            }
        ])

    return make_keyboard(buttons)


def get_lesson_type_keyboard():
    return make_keyboard([
        [
            {
                "type": "message",
                "text": "Онлайн / индивид",
                "message": "feedback:type:online"
            }
        ],
        [
            {
                "type": "message",
                "text": "Офлайн",
                "message": "feedback:type:offline"
            }
        ]
    ])


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}
    print("MAIN UPDATE:", data, flush=True)

    try:
        update_type = data.get("update_type")

        if update_type == "bot_started":
            chat_id = data.get("chat_id")

            if chat_id:
                response_text = bot.get_response("/start", user_id=str(chat_id))
                send_message(MAIN_TOKEN, chat_id, response_text, attachments=get_main_keyboard())

        elif update_type == "message_created":
            message = data.get("message", {})

            chat_id = message.get("recipient", {}).get("chat_id")
            user_id = message.get("sender", {}).get("user_id")
            text = (message.get("body", {}).get("text") or "").strip()

            if chat_id and user_id:
                response_text = bot.get_response(text, user_id=str(user_id))
                send_message(MAIN_TOKEN, chat_id, response_text, attachments=get_main_keyboard())

    except Exception as e:
        print("MAIN WEBHOOK ERROR:", str(e), flush=True)

    return jsonify({"status": "ok"}), 200


@app.route("/webhook/feedback", methods=["POST"])
def feedback_webhook():
    data = request.get_json(silent=True) or {}
    print("FEEDBACK UPDATE:", data, flush=True)

    try:
        update_type = data.get("update_type")

        if update_type == "bot_started":
            chat_id = data.get("chat_id")
            user_id = str(chat_id)

            if chat_id:
                send_message(
                    FEEDBACK_TOKEN,
                    chat_id,
                    "Здравствуйте! Нажмите кнопку, чтобы выбрать курс.",
                    attachments=get_feedback_start_keyboard()
                )

        elif update_type == "message_created":
            message = data.get("message", {})

            chat_id = message.get("recipient", {}).get("chat_id")
            user_id = str(message.get("sender", {}).get("user_id"))
            text = (message.get("body", {}).get("text") or "").strip()

            if not chat_id or not user_id:
                return jsonify({"status": "ok"}), 200

            if text == "feedback:course_list":
                send_message(
                    FEEDBACK_TOKEN,
                    chat_id,
                    "Выберите курс:",
                    attachments=get_courses_keyboard()
                )

            elif text.startswith("feedback:course:"):
                course_name = text.replace("feedback:course:", "", 1)

                feedback_bot.set_course(user_id, course_name)

                send_message(
                    FEEDBACK_TOKEN,
                    chat_id,
                    f"Курс выбран: {course_name}\nТеперь выберите номер урока:",
                    attachments=get_lessons_keyboard(course_name)
                )

            elif text.startswith("feedback:lesson:"):
                lesson_num = text.replace("feedback:lesson:", "", 1)

                feedback_bot.set_lesson(user_id, lesson_num)

                send_message(
                    FEEDBACK_TOKEN,
                    chat_id,
                    f"Урок выбран: №{lesson_num}\nТеперь выберите формат занятия:",
                    attachments=get_lesson_type_keyboard()
                )

            elif text == "feedback:type:online":
                result = feedback_bot.generate_feedback(user_id, "online")
                send_message(FEEDBACK_TOKEN, chat_id, result)

            elif text == "feedback:type:offline":
                result = feedback_bot.generate_feedback(user_id, "offline")
                send_message(FEEDBACK_TOKEN, chat_id, result)

            else:
                send_message(
                    FEEDBACK_TOKEN,
                    chat_id,
                    "Нажмите кнопку «Список курсов», чтобы начать.",
                    attachments=get_feedback_start_keyboard()
                )

    except Exception as e:
        print("FEEDBACK WEBHOOK ERROR:", str(e), flush=True)
        send_message(
            FEEDBACK_TOKEN,
            chat_id,
            "Произошла ошибка. Попробуйте начать заново.",
            attachments=get_feedback_start_keyboard()
        )

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
