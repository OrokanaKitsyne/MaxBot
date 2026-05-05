import os
import unittest
from unittest.mock import MagicMock, patch


os.environ["SUPABASE_URL"] = "https://example.supabase.co"
os.environ["SUPABASE_KEY"] = "fake-key"


class TestReminderBotLogic(unittest.TestCase):
    def create_logic(self):
        with patch("reminder_logic.ReminderDB") as mock_db_cls:
            from reminder_logic import ReminderBotLogic

            mock_db = MagicMock()
            mock_db_cls.return_value = mock_db

            logic = ReminderBotLogic()
            logic.db = mock_db

            return logic, mock_db

    def test_get_start_text_with_hello_payload(self):
        logic, _ = self.create_logic()

        result = logic.get_start_text("hello")

        self.assertIn("бот-напоминалка", result)
        self.assertIn("WEB2026", result)

    def test_get_start_text_without_payload(self):
        logic, _ = self.create_logic()

        result = logic.get_start_text("")

        self.assertIn("Пришлите код группы", result)

    def test_register_by_code_when_group_not_found(self):
        logic, mock_db = self.create_logic()
        mock_db.register_parent.return_value = None

        result = logic.register_by_code(
            chat_id=100,
            user_id="200",
            user_name="Иван",
            code="BADCODE"
        )

        self.assertEqual(result["chat_id"], 100)
        self.assertIn("Код группы не найден", result["text"])
        mock_db.register_parent.assert_called_once_with(
            "200",
            "Иван",
            "BADCODE",
            100
        )

    def test_register_by_code_success(self):
        logic, mock_db = self.create_logic()
        mock_db.register_parent.return_value = {
            "id": 1,
            "name": "WEB-1",
            "course_name": "Веб-разработка"
        }

        result = logic.register_by_code(
            chat_id=100,
            user_id="200",
            user_name="Иван",
            code="WEB2026"
        )

        self.assertEqual(result["chat_id"], 100)
        self.assertIn("Связь с таблицей установлена", result["text"])
        self.assertIn("WEB-1", result["text"])
        self.assertIn("Веб-разработка", result["text"])
        self.assertIn("attachments", result)

    def test_show_schedule_without_parent(self):
        logic, mock_db = self.create_logic()
        mock_db.get_parent.return_value = None

        result = logic.show_schedule(
            chat_id=100,
            user_id="200",
            callback_id="cb-1"
        )

        self.assertEqual(result["chat_id"], 100)
        self.assertEqual(result["callback_id"], "cb-1")
        self.assertIn("Сначала пришлите код группы", result["text"])

    def test_show_schedule_with_parent(self):
        logic, mock_db = self.create_logic()

        mock_db.get_parent.return_value = {
            "id": 1,
            "group_id": 10,
            "notifications_enabled": True,
            "groups": {
                "name": "PY-1",
                "course_name": "Python"
            }
        }

        mock_db.get_schedule.return_value = [
            {
                "lesson_number": 1,
                "lesson_date": "2026-05-05",
                "lesson_time": "12:30:00"
            }
        ]

        result = logic.show_schedule(
            chat_id=100,
            user_id="200",
            callback_id="cb-1"
        )

        self.assertEqual(result["chat_id"], 100)
        self.assertIn("PY-1", result["text"])
        self.assertIn("Python", result["text"])
        self.assertIn("Урок №1", result["text"])
        self.assertIn("Выключить уведомления", str(result["attachments"]))

    def test_enable_notifications_without_parent(self):
        logic, mock_db = self.create_logic()
        mock_db.get_parent.return_value = None

        result = logic.enable_notifications(
            chat_id=100,
            user_id="200",
            callback_id="cb-1"
        )

        self.assertIn("Сначала пришлите код группы", result["text"])
        mock_db.set_notifications.assert_not_called()

    def test_enable_notifications_success(self):
        logic, mock_db = self.create_logic()
        mock_db.get_parent.return_value = {
            "id": 1,
            "group_id": 10
        }

        result = logic.enable_notifications(
            chat_id=100,
            user_id="200",
            callback_id="cb-1"
        )

        self.assertIn("Уведомления включены", result["text"])
        self.assertIn("Выключить уведомления", str(result["attachments"]))
        mock_db.set_notifications.assert_called_once_with("200", True)

    def test_disable_notifications_without_parent(self):
        logic, mock_db = self.create_logic()
        mock_db.get_parent.return_value = None

        result = logic.disable_notifications(
            chat_id=100,
            user_id="200",
            callback_id="cb-1"
        )

        self.assertIn("Сначала пришлите код группы", result["text"])
        mock_db.set_notifications.assert_not_called()

    def test_disable_notifications_success(self):
        logic, mock_db = self.create_logic()
        mock_db.get_parent.return_value = {
            "id": 1,
            "group_id": 10
        }

        result = logic.disable_notifications(
            chat_id=100,
            user_id="200",
            callback_id="cb-1"
        )

        self.assertIn("Уведомления выключены", result["text"])
        self.assertIn("Включить уведомления", str(result["attachments"]))
        mock_db.set_notifications.assert_called_once_with("200", False)

    def test_save_feedback_rating_invalid_command(self):
        logic, _ = self.create_logic()

        result = logic.save_feedback_rating(
            chat_id=100,
            user_id="200",
            command="feedback:rating",
            callback_id="cb-1"
        )

        self.assertIn("Не удалось обработать оценку", result["text"])

    def test_save_feedback_rating_without_parent(self):
        logic, mock_db = self.create_logic()
        mock_db.get_parent.return_value = None

        result = logic.save_feedback_rating(
            chat_id=100,
            user_id="200",
            command="feedback:rating:15:5",
            callback_id="cb-1"
        )

        self.assertIn("Сначала пришлите код группы", result["text"])
        mock_db.save_feedback.assert_not_called()

    def test_save_feedback_rating_success(self):
        logic, mock_db = self.create_logic()
        mock_db.get_parent.return_value = {
            "id": 7,
            "group_id": 10
        }

        result = logic.save_feedback_rating(
            chat_id=100,
            user_id="200",
            command="feedback:rating:15:5",
            callback_id="cb-1"
        )

        self.assertIn("Спасибо за оценку", result["text"])
        self.assertIn("⭐⭐⭐⭐⭐", result["text"])
        self.assertIn("Добавить комментарий", str(result["attachments"]))
        mock_db.save_feedback.assert_called_once_with(7, "15", 5)

    def test_ask_comment_invalid_command(self):
        logic, _ = self.create_logic()

        result = logic.ask_comment(
            chat_id=100,
            user_id="200",
            command="feedback:comment",
            callback_id="cb-1"
        )

        self.assertIn("Не удалось начать добавление комментария", result["text"])

    def test_ask_comment_success(self):
        logic, mock_db = self.create_logic()

        result = logic.ask_comment(
            chat_id=100,
            user_id="200",
            command="feedback:comment:15",
            callback_id="cb-1"
        )

        self.assertIn("Напишите комментарий", result["text"])
        self.assertEqual(result["attachments"], [])
        mock_db.set_waiting_for_comment.assert_called_once_with("200", "15")

    def test_save_comment_without_parent(self):
        logic, mock_db = self.create_logic()
        mock_db.get_parent.return_value = None

        result = logic.save_comment(
            chat_id=100,
            user_id="200",
            comment="Хороший урок"
        )

        self.assertIn("Сначала пришлите код группы", result["text"])

    def test_save_comment_without_pending_lesson(self):
        logic, mock_db = self.create_logic()
        mock_db.get_parent.return_value = {
            "id": 7,
            "pending_feedback_lesson_id": None
        }

        result = logic.save_comment(
            chat_id=100,
            user_id="200",
            comment="Хороший урок"
        )

        self.assertIn("Не найден урок для комментария", result["text"])

    def test_save_comment_success(self):
        logic, mock_db = self.create_logic()
        mock_db.get_parent.return_value = {
            "id": 7,
            "pending_feedback_lesson_id": 15,
            "notifications_enabled": True
        }

        result = logic.save_comment(
            chat_id=100,
            user_id="200",
            comment="Хороший урок"
        )

        self.assertIn("Комментарий сохранён", result["text"])
        self.assertIn("Выключить уведомления", str(result["attachments"]))

        mock_db.save_feedback_comment.assert_called_once_with(
            7,
            15,
            "Хороший урок"
        )
        mock_db.clear_waiting_for_comment.assert_called_once_with("200")

    def test_skip_comment_with_parent(self):
        logic, mock_db = self.create_logic()
        mock_db.get_parent.return_value = {
            "id": 7,
            "notifications_enabled": False
        }

        result = logic.skip_comment(
            chat_id=100,
            user_id="200",
            callback_id="cb-1"
        )

        self.assertIn("Спасибо за отзыв", result["text"])
        self.assertIn("Включить уведомления", str(result["attachments"]))
        mock_db.clear_waiting_for_comment.assert_called_once_with("200")

    def test_skip_comment_without_parent(self):
        logic, mock_db = self.create_logic()
        mock_db.get_parent.return_value = None

        result = logic.skip_comment(
            chat_id=100,
            user_id="200",
            callback_id="cb-1"
        )

        self.assertIn("Спасибо за отзыв", result["text"])
        self.assertIn("Включить уведомления", str(result["attachments"]))
        mock_db.clear_waiting_for_comment.assert_not_called()

    def test_format_schedule_empty(self):
        logic, _ = self.create_logic()

        result = logic.format_schedule([])

        self.assertEqual(result, "Расписание пока не добавлено 🕓")

    def test_format_schedule_with_lessons(self):
        logic, _ = self.create_logic()

        result = logic.format_schedule([
            {
                "lesson_number": 1,
                "lesson_date": "2026-05-05",
                "lesson_time": "12:30:00"
            },
            {
                "lesson_number": 2,
                "lesson_date": "2026-05-06",
                "lesson_time": "13:45:00"
            }
        ])

        self.assertIn("Расписание занятий", result)
        self.assertIn("Урок №1", result)
        self.assertIn("2026-05-05 в 12:30", result)
        self.assertIn("Урок №2", result)
        self.assertIn("2026-05-06 в 13:45", result)

    def test_get_keyboard_when_notifications_enabled(self):
        logic, _ = self.create_logic()

        keyboard = logic.get_keyboard(True)

        self.assertIn("Посмотреть всё расписание", str(keyboard))
        self.assertIn("Выключить уведомления", str(keyboard))
        self.assertIn("reminder:notifications_off", str(keyboard))

    def test_get_keyboard_when_notifications_disabled(self):
        logic, _ = self.create_logic()

        keyboard = logic.get_keyboard(False)

        self.assertIn("Посмотреть всё расписание", str(keyboard))
        self.assertIn("Включить уведомления", str(keyboard))
        self.assertIn("reminder:notifications_on", str(keyboard))

    def test_extract_event_from_bot_started(self):
        logic, _ = self.create_logic()

        data = {
            "update_type": "bot_started",
            "chat_id": 100,
            "user": {
                "user_id": 200,
                "name": "Иван"
            },
            "payload": "hello"
        }

        event = logic.extract_event(data)

        self.assertEqual(event["update_type"], "bot_started")
        self.assertEqual(event["chat_id"], 100)
        self.assertEqual(event["user_id"], "200")
        self.assertEqual(event["user_name"], "Иван")
        self.assertEqual(event["command"], "hello")

    def test_extract_event_from_message_created(self):
        logic, _ = self.create_logic()

        data = {
            "update_type": "message_created",
            "message": {
                "recipient": {
                    "chat_id": 100
                },
                "sender": {
                    "user_id": 200,
                    "name": "Иван"
                },
                "body": {
                    "text": "WEB2026"
                }
            }
        }

        event = logic.extract_event(data)

        self.assertEqual(event["update_type"], "message_created")
        self.assertEqual(event["chat_id"], 100)
        self.assertEqual(event["user_id"], "200")
        self.assertEqual(event["command"], "WEB2026")

    def test_extract_event_from_message_callback(self):
        logic, _ = self.create_logic()

        data = {
            "update_type": "message_callback",
            "callback": {
                "chat_id": 100,
                "callback_id": "cb-1",
                "payload": "reminder:schedule",
                "user": {
                    "user_id": 200,
                    "name": "Иван"
                }
            }
        }

        event = logic.extract_event(data)

        self.assertEqual(event["update_type"], "message_callback")
        self.assertEqual(event["chat_id"], 100)
        self.assertEqual(event["user_id"], "200")
        self.assertEqual(event["command"], "reminder:schedule")
        self.assertEqual(event["callback_id"], "cb-1")

    def test_handle_update_without_chat_id_returns_none(self):
        logic, _ = self.create_logic()

        result = logic.handle_update({
            "update_type": "message_created",
            "message": {
                "sender": {
                    "user_id": 200
                },
                "body": {
                    "text": "WEB2026"
                }
            }
        })

        self.assertIsNone(result)

    def test_handle_update_bot_started(self):
        logic, _ = self.create_logic()

        result = logic.handle_update({
            "update_type": "bot_started",
            "chat_id": 100,
            "user": {
                "user_id": 200,
                "name": "Иван"
            },
            "payload": "hello"
        })

        self.assertEqual(result["chat_id"], 100)
        self.assertIn("бот-напоминалка", result["text"])

    def test_handle_update_unknown_update_type_returns_none(self):
        logic, _ = self.create_logic()

        result = logic.handle_update({
            "update_type": "unknown",
            "chat_id": 100,
            "user": {
                "user_id": 200,
                "name": "Иван"
            }
        })

        self.assertIsNone(result)

    def test_handle_update_message_created_waiting_for_comment(self):
        logic, mock_db = self.create_logic()
        mock_db.get_parent.return_value = {
            "id": 7,
            "waiting_for_comment": True,
            "pending_feedback_lesson_id": 15,
            "notifications_enabled": False
        }

        result = logic.handle_update({
            "update_type": "message_created",
            "message": {
                "recipient": {
                    "chat_id": 100
                },
                "sender": {
                    "user_id": 200,
                    "name": "Иван"
                },
                "body": {
                    "text": "Всё понравилось"
                }
            }
        })

        self.assertIn("Комментарий сохранён", result["text"])
        mock_db.save_feedback_comment.assert_called_once_with(
            7,
            15,
            "Всё понравилось"
        )

    def test_handle_update_schedule_command(self):
        logic, mock_db = self.create_logic()
        mock_db.get_parent.return_value = {
            "id": 7,
            "group_id": 10,
            "notifications_enabled": False,
            "groups": {
                "name": "PY-1",
                "course_name": "Python"
            }
        }
        mock_db.get_schedule.return_value = []

        result = logic.handle_update({
            "update_type": "message_callback",
            "callback": {
                "chat_id": 100,
                "callback_id": "cb-1",
                "payload": "reminder:schedule",
                "user": {
                    "user_id": 200,
                    "name": "Иван"
                }
            }
        })

        self.assertIn("PY-1", result["text"])
        self.assertIn("Расписание пока не добавлено", result["text"])

    def test_handle_update_register_by_code(self):
        logic, mock_db = self.create_logic()
        mock_db.get_parent.return_value = None
        mock_db.register_parent.return_value = {
            "id": 1,
            "name": "WEB-1",
            "course_name": "Веб-разработка"
        }

        result = logic.handle_update({
            "update_type": "message_created",
            "message": {
                "recipient": {
                    "chat_id": 100
                },
                "sender": {
                    "user_id": 200,
                    "name": "Иван"
                },
                "body": {
                    "text": "WEB2026"
                }
            }
        })

        self.assertIn("Связь с таблицей установлена", result["text"])
        mock_db.register_parent.assert_called_once_with(
            "200",
            "Иван",
            "WEB2026",
            100
        )


if __name__ == "__main__":
    unittest.main()
