import os
import unittest
from unittest.mock import MagicMock, patch


os.environ["SUPABASE_URL"] = "https://example.supabase.co"
os.environ["SUPABASE_KEY"] = "fake-key"


class TestReminderScheduler(unittest.TestCase):
    def setUp(self):
        import reminder_scheduler

        self.reminder_scheduler = reminder_scheduler
        self.scheduler = reminder_scheduler.ReminderScheduler(token="test-token")

        self.mock_supabase = MagicMock()
        self.reminder_scheduler.supabase = self.mock_supabase

    def make_chain(self, data=None):
        chain = MagicMock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.update.return_value = chain

        result = MagicMock()
        result.data = data if data is not None else []
        chain.execute.return_value = result

        return chain

    def test_get_lesson_title_returns_title(self):
        self.reminder_scheduler.FEEDBACK_LESSONS = {
            "courses": {
                "Python": {
                    "lessons": {
                        "1": {
                            "title": "Переменные"
                        }
                    }
                }
            }
        }

        title = self.reminder_scheduler.get_lesson_title("Python", 1)

        self.assertEqual(title, "Переменные")

    def test_get_lesson_title_returns_default_when_missing(self):
        self.reminder_scheduler.FEEDBACK_LESSONS = {
            "courses": {}
        }

        title = self.reminder_scheduler.get_lesson_title("Python", 1)

        self.assertEqual(title, "Тема урока не указана")

    def test_get_feedback_keyboard_contains_five_rating_buttons(self):
        keyboard = self.scheduler.get_feedback_keyboard(lesson_id=15)

        self.assertIsInstance(keyboard, list)
        self.assertEqual(keyboard[0]["type"], "inline_keyboard")

        buttons = keyboard[0]["payload"]["buttons"]
        flat_buttons = [button for row in buttons for button in row]

        self.assertEqual(len(flat_buttons), 5)
        self.assertEqual(flat_buttons[0]["payload"], "feedback:rating:15:1")
        self.assertEqual(flat_buttons[-1]["payload"], "feedback:rating:15:5")

    def test_get_active_parents_returns_data(self):
        parents = [
            {
                "id": 1,
                "chat_id": 111,
                "notifications_enabled": True
            }
        ]

        chain = self.make_chain(data=parents)
        self.mock_supabase.table.return_value = chain

        result = self.scheduler.get_active_parents(group_id=10)

        self.assertEqual(result, parents)
        self.mock_supabase.table.assert_called_once_with("parents")

        calls = chain.eq.call_args_list
        self.assertEqual(calls[0].args, ("group_id", 10))
        self.assertEqual(calls[1].args, ("notifications_enabled", True))

    def test_mark_reminder_sent_updates_lesson(self):
        chain = self.make_chain()
        self.mock_supabase.table.return_value = chain

        self.scheduler.mark_reminder_sent(lesson_id=5)

        self.mock_supabase.table.assert_called_once_with("lessons")
        chain.update.assert_called_once_with({"reminder_sent": True})
        chain.eq.assert_called_once_with("id", 5)
        chain.execute.assert_called_once()

    def test_mark_feedback_requested_updates_lesson(self):
        chain = self.make_chain()
        self.mock_supabase.table.return_value = chain

        self.scheduler.mark_feedback_requested(lesson_id=5)

        self.mock_supabase.table.assert_called_once_with("lessons")
        chain.update.assert_called_once_with({"feedback_requested": True})
        chain.eq.assert_called_once_with("id", 5)
        chain.execute.assert_called_once()

    @patch("reminder_scheduler.send_message")
    def test_send_lesson_reminder_sends_message_to_active_parents(self, mock_send_message):
        self.reminder_scheduler.FEEDBACK_LESSONS = {
            "courses": {
                "Python": {
                    "lessons": {
                        "1": {
                            "title": "Переменные"
                        }
                    }
                }
            }
        }

        parents = [
            {
                "chat_id": 111
            },
            {
                "chat_id": None
            },
            {
                "chat_id": 222
            }
        ]

        lesson = {
            "id": 1,
            "group_id": 10,
            "lesson_number": 1,
            "lesson_date": "2026-05-05",
            "lesson_time": "12:30:00",
            "groups": {
                "course_name": "Python"
            }
        }

        with patch.object(self.scheduler, "get_active_parents", return_value=parents):
            self.scheduler.send_lesson_reminder(lesson)

        self.assertEqual(mock_send_message.call_count, 2)

        first_call = mock_send_message.call_args_list[0]
        self.assertEqual(first_call.args[0], "test-token")
        self.assertEqual(first_call.args[1], 111)
        self.assertIn("Напоминание о занятии", first_call.args[2])
        self.assertIn("Курс: Python", first_call.args[2])
        self.assertIn("Тема: Переменные", first_call.args[2])

    @patch("reminder_scheduler.send_message")
    def test_send_feedback_request_sends_message_with_keyboard(self, mock_send_message):
        self.reminder_scheduler.FEEDBACK_LESSONS = {
            "courses": {
                "Python": {
                    "lessons": {
                        "1": {
                            "title": "Переменные"
                        }
                    }
                }
            }
        }

        parents = [
            {
                "chat_id": 111
            }
        ]

        lesson = {
            "id": 15,
            "group_id": 10,
            "lesson_number": 1,
            "lesson_date": "2026-05-05",
            "lesson_time": "12:30:00",
            "groups": {
                "course_name": "Python"
            }
        }

        with patch.object(self.scheduler, "get_active_parents", return_value=parents):
            self.scheduler.send_feedback_request(lesson)

        mock_send_message.assert_called_once()

        call = mock_send_message.call_args
        self.assertEqual(call.args[0], "test-token")
        self.assertEqual(call.args[1], 111)
        self.assertIn("Обратная связь по занятию", call.args[2])
        self.assertIn("Пожалуйста, оцените занятие", call.args[2])

        attachments = call.kwargs["attachments"]
        self.assertEqual(
            attachments[0]["payload"]["buttons"][0][0]["payload"],
            "feedback:rating:15:1"
        )

    def test_check_lessons_calls_both_checks(self):
        with patch.object(self.scheduler, "check_reminders") as mock_check_reminders:
            with patch.object(self.scheduler, "check_feedback_requests") as mock_check_feedback:
                self.scheduler.check_lessons()

        mock_check_reminders.assert_called_once()
        mock_check_feedback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
