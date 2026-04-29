from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from reminder_db import supabase
from max_api import send_message


TIMEZONE = ZoneInfo("Europe/Moscow")


class ReminderScheduler:
    def __init__(self, token):
        self.token = token

    def check_lessons(self):
        now = datetime.now(TIMEZONE)

        today = now.date()
        tomorrow = today + timedelta(days=1)

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
                self.send_lesson_reminder(lesson)
                self.mark_reminder_sent(lesson["id"])

    def send_lesson_reminder(self, lesson):
        group_id = lesson["group_id"]

        parents_result = (
            supabase
            .table("parents")
            .select("*")
            .eq("group_id", group_id)
            .eq("notifications_enabled", True)
            .execute()
        )

        parents = parents_result.data or []

        for parent in parents:
            chat_id = parent.get("chat_id")

            if not chat_id:
                continue

            text = (
                f"Напоминание о занятии.\n\n"
                f"Завтра состоится урок №{lesson['lesson_number']}.\n"
                f"Дата: {lesson['lesson_date']}\n"
                f"Время: {lesson['lesson_time']}"
            )

            send_message(self.token, chat_id, text)

    def mark_reminder_sent(self, lesson_id):
        (
            supabase
            .table("lessons")
            .update({"reminder_sent": True})
            .eq("id", lesson_id)
            .execute()
        )
