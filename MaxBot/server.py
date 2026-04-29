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

reminder_scheduler = ReminderScheduler(REMINDER_TOKEN)

scheduler = BackgroundScheduler(timezone="Europe/Moscow")
scheduler.add_job(
    reminder_scheduler.check_lessons,
    "interval",
    minutes=1
)
scheduler.start()

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

    chat_id = None

    try:
        event = extract_feedback_event(data)

        update_type = event["update_type"]
        chat_id = event["chat_id"]
        user_id = event["user_id"] or str(chat_id)
        command = event["command"]
        callback_id = event["callback_id"]

        print("COMMAND:", command, flush=True)
        print("CHAT ID:", chat_id, flush=True)
        print("USER ID:", user_id, flush=True)
        print("CALLBACK ID:", callback_id, flush=True)

        if not chat_id:
            return jsonify({"status": "ok"}), 200

        if update_type == "bot_started":
            send_message(
                FEEDBACK_TOKEN,
                chat_id,
                "Здравствуйте! Нажмите кнопку, чтобы выбрать курс.",
                attachments=get_feedback_start_keyboard()
            )
            return jsonify({"status": "ok"}), 200

        if command in ("feedback:course_list", "список курсов", "/start", "start"):
            answer_or_send(
                FEEDBACK_TOKEN,
                chat_id,
                callback_id,
                "Выберите курс:",
                attachments=get_courses_keyboard()
            )

        elif command == "feedback:lesson_list":
            state = feedback_bot.get_state(user_id)
            course_name = state.get("course")

            if not course_name:
                answer_or_send(
                    FEEDBACK_TOKEN,
                    chat_id,
                    callback_id,
                    "Сначала выберите курс:",
                    attachments=get_courses_keyboard()
                )
            else:
                answer_or_send(
                    FEEDBACK_TOKEN,
                    chat_id,
                    callback_id,
                    f"Курс: {course_name}\nВыберите номер урока:",
                    attachments=get_lessons_keyboard(course_name)
                )

        elif command.startswith("feedback:course:"):
            course_name = command.replace("feedback:course:", "", 1).strip()

            print("SELECTED COURSE:", course_name, flush=True)

            if not feedback_bot.course_exists(course_name):
                answer_or_send(
                    FEEDBACK_TOKEN,
                    chat_id,
                    callback_id,
                    "Курс не найден. Выберите курс из списка:",
                    attachments=get_courses_keyboard()
                )
            else:
                feedback_bot.set_course(user_id, course_name)

                answer_or_send(
                    FEEDBACK_TOKEN,
                    chat_id,
                    callback_id,
                    f"Курс выбран: {course_name}\nТеперь выберите номер урока:",
                    attachments=get_lessons_keyboard(course_name)
                )

        elif command.startswith("feedback:lesson:"):
            lesson_num = command.replace("feedback:lesson:", "", 1).strip()
            state = feedback_bot.get_state(user_id)
            course_name = state.get("course")

            if not course_name:
                answer_or_send(
                    FEEDBACK_TOKEN,
                    chat_id,
                    callback_id,
                    "Сначала выберите курс:",
                    attachments=get_courses_keyboard()
                )
            elif not feedback_bot.lesson_exists(course_name, lesson_num):
                answer_or_send(
                    FEEDBACK_TOKEN,
                    chat_id,
                    callback_id,
                    "Урок не найден. Выберите урок из списка:",
                    attachments=get_lessons_keyboard(course_name)
                )
            else:
                feedback_bot.set_lesson(user_id, lesson_num)

                answer_or_send(
                    FEEDBACK_TOKEN,
                    chat_id,
                    callback_id,
                    f"Курс: {course_name}\nУрок: №{lesson_num}\nТеперь выберите формат занятия:",
                    attachments=get_lesson_type_keyboard()
                )

        elif command == "feedback:type:online":
            result = feedback_bot.generate_feedback(user_id, "online")

            answer_or_send(
                FEEDBACK_TOKEN,
                chat_id,
                callback_id,
                result,
                attachments=get_feedback_result_keyboard()
            )

        elif command == "feedback:type:offline":
            result = feedback_bot.generate_feedback(user_id, "offline")

            answer_or_send(
                FEEDBACK_TOKEN,
                chat_id,
                callback_id,
                result,
                attachments=get_feedback_result_keyboard()
            )

        else:
            answer_or_send(
                FEEDBACK_TOKEN,
                chat_id,
                callback_id,
                "Нажмите кнопку «Список курсов», чтобы начать.",
                attachments=get_feedback_start_keyboard()
            )

    except Exception as e:
        print("FEEDBACK WEBHOOK ERROR:", str(e), flush=True)

        if chat_id:
            send_message(
                FEEDBACK_TOKEN,
                chat_id,
                "Произошла ошибка. Попробуйте начать заново.",
                attachments=get_feedback_start_keyboard()
            )

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
