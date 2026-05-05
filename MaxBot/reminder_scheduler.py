from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json

from reminder_db import supabase
from max_api import send_message


TIMEZONE = ZoneInfo("Europe/Moscow")
FEEDBACK_LESSONS_FILE = "feedback_lessons.json"


def load_feedback_lessons():
    try:
        with open(FEEDBACK_LESSONS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        print("FEEDBACK LESSONS LOAD ERROR:", str(e), flush=True)
        return {"courses": {}}


FEEDBACK_LESSONS = load_feedback_lessons()


def get_lesson_title(course_name, lesson_number):
    try:
        return (
            FEEDBACK_LESSONS["courses"]
            [course_name]
            ["lessons"]
            [str(lesson_number)]
            ["title"]
        )
    except Exception:
        return "Тема урока не указана"


class ReminderScheduler:
    def __init__(self, token):
        self.token = token

    def check_lessons(self):
        print("Checking lessons...", flush=True)

        self.check_reminders()
        self.check_feedback_requests()

    def check_reminders(self):
        now = datetime.now(TIMEZONE)
        tomorrow = now.date() + timedelta(days=1)

        lessons_result = (
            supabase
            .table("lessons")
            .select("*, groups(*)")
            .eq("lesson_date", str(tomorrow))
            .eq("reminder_sent", False)
            .execute()
        )

        lessons = lessons_result.data or []

        for lesson in lessons:
            lesson_datetime = datetime.fromisoformat(
                f"{lesson['lesson_date']}T{lesson['lesson_time']}"
            ).replace(tzinfo=TIMEZONE)

            reminder_time = lesson_datetime - timedelta(days=1)

            if now >= reminder_time:
                print(f"Sending reminder for lesson {lesson['lesson_number']}", flush=True)

                self.send_lesson_reminder(lesson)
                self.mark_reminder_sent(lesson["id"])

    def check_feedback_requests(self):
        print("Checking feedback requests...", flush=True)

        now = datetime.now(TIMEZONE)

        lessons_result = (
            supabase
            .table("lessons")
            .select("*, groups(*)")
            .eq("lesson_date", str(now.date()))
            .eq("feedback_requested", False)
            .execute()
        )

        lessons = lessons_result.data or []

        for lesson in lessons:
            lesson_datetime = datetime.fromisoformat(
                f"{lesson['lesson_date']}T{lesson['lesson_time']}"
            ).replace(tzinfo=TIMEZONE)

            feedback_time = lesson_datetime + timedelta(hours=1, minutes=30)

            if now >= feedback_time:
                print(f"Sending feedback request for lesson {lesson['lesson_number']}", flush=True)

                self.send_feedback_request(lesson)
                self.mark_feedback_requested(lesson["id"])

    def send_lesson_reminder(self, lesson):
        parents = self.get_active_parents(lesson["group_id"])
        lesson_time = str(lesson["lesson_time"])[:5]

        group = lesson.get("groups") or {}
        course_name = group.get("course_name", "Курс не указан")
        lesson_title = get_lesson_title(course_name, lesson["lesson_number"])

        for parent in parents:
            chat_id = parent.get("chat_id")

            if not chat_id:
                continue

            text = (
                "📚 Напоминание о занятии\n\n"
                "Здравствуйте! 😊\n\n"
                f"Завтра состоится урок №{lesson['lesson_number']}.\n\n"
                f"📚 Курс: {course_name}\n"
                f"📝 Тема: {lesson_title}\n"
                f"📅 Дата: {lesson['lesson_date']}\n"
                f"⏰ Время: {lesson_time}\n\n"
                "Ждём вас на занятии! 🚀"
            )

            send_message(self.token, chat_id, text)

    def send_feedback_request(self, lesson):
        parents = self.get_active_parents(lesson["group_id"])

        group = lesson.get("groups") or {}
        course_name = group.get("course_name", "Курс не указан")
        lesson_title = get_lesson_title(course_name, lesson["lesson_number"])

        for parent in parents:
            chat_id = parent.get("chat_id")

            if not chat_id:
                continue

            text = (
                "⭐ Обратная связь по занятию\n\n"
                "Здравствуйте! 😊\n\n"
                f"Урок №{lesson['lesson_number']} уже завершился.\n\n"
                f"📚 Курс: {course_name}\n"
                f"📝 Тема: {lesson_title}\n\n"
                "Пожалуйста, оцените занятие:"
            )

            send_message(
                self.token,
                chat_id,
                text,
                attachments=self.get_feedback_keyboard(lesson["id"])
            )

    def get_feedback_keyboard(self, lesson_id):
        return [
            {
                "type": "inline_keyboard",
                "payload": {
                    "buttons": [
                        [
                            {
                                "type": "callback",
                                "text": "⭐ 1",
                                "payload": f"feedback:rating:{lesson_id}:1"
                            },
                            {
                                "type": "callback",
                                "text": "⭐ 2",
                                "payload": f"feedback:rating:{lesson_id}:2"
                            },
                            {
                                "type": "callback",
                                "text": "⭐ 3",
                                "payload": f"feedback:rating:{lesson_id}:3"
                            }
                        ],
                        [
                            {
                                "type": "callback",
                                "text": "⭐ 4",
                                "payload": f"feedback:rating:{lesson_id}:4"
                            },
                            {
                                "type": "callback",
                                "text": "⭐ 5",
                                "payload": f"feedback:rating:{lesson_id}:5"
                            }
                        ]
                    ]
                }
            }
        ]

    def get_active_parents(self, group_id):
        parents_result = (
            supabase
            .table("parents")
            .select("*")
            .eq("group_id", group_id)
            .eq("notifications_enabled", True)
            .execute()
        )

        return parents_result.data or []

    def mark_reminder_sent(self, lesson_id):
        (
            supabase
            .table("lessons")
            .update({"reminder_sent": True})
            .eq("id", lesson_id)
            .execute()
        )

    def mark_feedback_requested(self, lesson_id):
        (
            supabase
            .table("lessons")
            .update({"feedback_requested": True})
            .eq("id", lesson_id)
            .execute()
        )
