import importlib
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


class DummyScheduler:
    def __init__(self, *args, **kwargs):
        self.jobs = []
        self.started = False

    def add_job(self, *args, **kwargs):
        self.jobs.append((args, kwargs))

    def start(self):
        self.started = True


class TestServer(unittest.TestCase):
    def import_server(self):
        os.environ["MAX_BOT_TOKEN"] = "main-token"
        os.environ["MAX_FEEDBACK_BOT_TOKEN"] = "feedback-token"
        os.environ["MAX_REMINDER_BOT_TOKEN"] = "reminder-token"

        fake_max_api = types.ModuleType("max_api")
        fake_max_api.send_message = MagicMock()
        fake_max_api.answer_callback = MagicMock()

        fake_bot_logic = types.ModuleType("bot_logic")
        fake_feedback_logic = types.ModuleType("feedback_logic")
        fake_reminder_logic = types.ModuleType("reminder_logic")
        fake_reminder_scheduler = types.ModuleType("reminder_scheduler")

        fake_apscheduler = types.ModuleType("apscheduler")
        fake_apscheduler_schedulers = types.ModuleType("apscheduler.schedulers")
        fake_apscheduler_background = types.ModuleType("apscheduler.schedulers.background")
        fake_apscheduler_background.BackgroundScheduler = DummyScheduler

        class FakeBotLogic:
            def __init__(self):
                self.get_response = MagicMock(return_value="Ответ основного бота")

        class FakeFeedbackBotLogic:
            def __init__(self):
                self.get_courses = MagicMock(return_value=["Python", "Геймдизайн"])
                self.get_lessons = MagicMock(return_value=["1", "2", "3", "4", "5"])
                self.get_state = MagicMock(return_value={})
                self.course_exists = MagicMock(return_value=True)
                self.lesson_exists = MagicMock(return_value=True)
                self.set_course = MagicMock()
                self.set_lesson = MagicMock()
                self.generate_feedback = MagicMock(return_value="Текст обратной связи")

        class FakeReminderBotLogic:
            def __init__(self):
                self.handle_update = MagicMock(return_value=None)

        class FakeReminderScheduler:
            def __init__(self, token):
                self.token = token
                self.check_lessons = MagicMock()

        fake_bot_logic.BotLogic = FakeBotLogic
        fake_feedback_logic.FeedbackBotLogic = FakeFeedbackBotLogic
        fake_reminder_logic.ReminderBotLogic = FakeReminderBotLogic
        fake_reminder_scheduler.ReminderScheduler = FakeReminderScheduler

        modules = {
            "max_api": fake_max_api,
            "bot_logic": fake_bot_logic,
            "feedback_logic": fake_feedback_logic,
            "reminder_logic": fake_reminder_logic,
            "reminder_scheduler": fake_reminder_scheduler,
            "apscheduler": fake_apscheduler,
            "apscheduler.schedulers": fake_apscheduler_schedulers,
            "apscheduler.schedulers.background": fake_apscheduler_background,
        }

        patcher = patch.dict(sys.modules, modules)
        patcher.start()
        self.addCleanup(patcher.stop)

        sys.modules.pop("server", None)

        server = importlib.import_module("server")
        return server

    def test_health_route(self):
        server = self.import_server()
        client = server.app.test_client()

        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode(), "OK")

    def test_home_route(self):
        server = self.import_server()
        client = server.app.test_client()

        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode(), "Bot is running")

    def test_make_keyboard(self):
        server = self.import_server()

        keyboard = server.make_keyboard([
            [
                {
                    "type": "callback",
                    "text": "Кнопка",
                    "payload": "payload"
                }
            ]
        ])

        self.assertEqual(keyboard[0]["type"], "inline_keyboard")
        self.assertEqual(keyboard[0]["payload"]["buttons"][0][0]["text"], "Кнопка")

    def test_message_button(self):
        server = self.import_server()

        button = server.message_button("Список курсов", "список курсов")

        self.assertEqual(button["type"], "message")
        self.assertEqual(button["text"], "Список курсов")
        self.assertEqual(button["message"], "список курсов")

    def test_callback_button(self):
        server = self.import_server()

        button = server.callback_button("Кнопка", "payload")

        self.assertEqual(button["type"], "callback")
        self.assertEqual(button["text"], "Кнопка")
        self.assertEqual(button["payload"], "payload")

    def test_get_main_keyboard(self):
        server = self.import_server()

        keyboard = server.get_main_keyboard()

        text = str(keyboard)
        self.assertIn("Список курсов", text)
        self.assertIn("Контакты", text)
        self.assertIn("Помощь", text)
        self.assertIn("Записаться", text)

    def test_get_feedback_start_keyboard(self):
        server = self.import_server()

        keyboard = server.get_feedback_start_keyboard()

        self.assertIn("Список курсов", str(keyboard))
        self.assertIn("feedback:course_list", str(keyboard))

    def test_get_courses_keyboard(self):
        server = self.import_server()

        keyboard = server.get_courses_keyboard()

        self.assertIn("Python", str(keyboard))
        self.assertIn("Геймдизайн", str(keyboard))
        self.assertIn("feedback:course:Python", str(keyboard))

    def test_get_lessons_keyboard_groups_buttons_and_back_button(self):
        server = self.import_server()
        server.feedback_bot.get_lessons.return_value = ["1", "2", "3", "4", "5"]

        keyboard = server.get_lessons_keyboard("Python")
        buttons = keyboard[0]["payload"]["buttons"]

        self.assertEqual(len(buttons[0]), 4)
        self.assertEqual(len(buttons[1]), 1)
        self.assertEqual(buttons[0][0]["payload"], "feedback:lesson:1")
        self.assertIn("← К курсам", str(keyboard))

    def test_get_lesson_type_keyboard(self):
        server = self.import_server()

        keyboard = server.get_lesson_type_keyboard()

        self.assertIn("Онлайн / индивид", str(keyboard))
        self.assertIn("Офлайн", str(keyboard))
        self.assertIn("feedback:type:online", str(keyboard))
        self.assertIn("feedback:type:offline", str(keyboard))

    def test_get_feedback_result_keyboard(self):
        server = self.import_server()

        keyboard = server.get_feedback_result_keyboard()

        self.assertIn("← К курсам", str(keyboard))
        self.assertIn("← К урокам", str(keyboard))

    def test_get_from_paths_returns_first_existing_value(self):
        server = self.import_server()

        data = {
            "message": {
                "recipient": {
                    "chat_id": 123
                }
            }
        }

        result = server.get_from_paths(data, [
            ["chat_id"],
            ["message", "recipient", "chat_id"]
        ])

        self.assertEqual(result, 123)

    def test_get_from_paths_returns_none_when_not_found(self):
        server = self.import_server()

        result = server.get_from_paths(
            {"message": {}},
            [["message", "recipient", "chat_id"]]
        )

        self.assertIsNone(result)

    def test_extract_feedback_event_from_message_created(self):
        server = self.import_server()

        data = {
            "update_type": "message_created",
            "message": {
                "recipient": {
                    "chat_id": 123
                },
                "sender": {
                    "user_id": 456
                },
                "body": {
                    "text": "список курсов"
                }
            }
        }

        event = server.extract_feedback_event(data)

        self.assertEqual(event["update_type"], "message_created")
        self.assertEqual(event["chat_id"], 123)
        self.assertEqual(event["user_id"], "456")
        self.assertEqual(event["command"], "список курсов")
        self.assertIsNone(event["callback_id"])

    def test_extract_feedback_event_from_callback(self):
        server = self.import_server()

        data = {
            "update_type": "message_callback",
            "callback": {
                "chat_id": 123,
                "payload": "feedback:course_list",
                "callback_id": "cb-1",
                "user": {
                    "user_id": 456
                }
            }
        }

        event = server.extract_feedback_event(data)

        self.assertEqual(event["chat_id"], 123)
        self.assertEqual(event["user_id"], "456")
        self.assertEqual(event["command"], "feedback:course_list")
        self.assertEqual(event["callback_id"], "cb-1")

    def test_answer_or_send_uses_answer_callback_when_successful(self):
        server = self.import_server()

        response = MagicMock()
        response.status_code = 200
        server.answer_callback.return_value = response

        result = server.answer_or_send(
            token="token",
            chat_id=123,
            callback_id="cb-1",
            text="Ответ"
        )

        self.assertEqual(result, response)
        server.answer_callback.assert_called_once()
        server.send_message.assert_not_called()

    def test_answer_or_send_falls_back_to_send_message_when_callback_failed(self):
        server = self.import_server()

        callback_response = MagicMock()
        callback_response.status_code = 500
        send_response = MagicMock()

        server.answer_callback.return_value = callback_response
        server.send_message.return_value = send_response

        result = server.answer_or_send(
            token="token",
            chat_id=123,
            callback_id="cb-1",
            text="Ответ"
        )

        self.assertEqual(result, send_response)
        server.answer_callback.assert_called_once()
        server.send_message.assert_called_once()

    def test_answer_or_send_without_callback_uses_send_message(self):
        server = self.import_server()

        send_response = MagicMock()
        server.send_message.return_value = send_response

        result = server.answer_or_send(
            token="token",
            chat_id=123,
            callback_id=None,
            text="Ответ"
        )

        self.assertEqual(result, send_response)
        server.answer_callback.assert_not_called()
        server.send_message.assert_called_once()

    def test_main_webhook_bot_started(self):
        server = self.import_server()
        client = server.app.test_client()

        response = client.post("/webhook", json={
            "update_type": "bot_started",
            "chat_id": 123
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})

        server.bot.get_response.assert_called_once_with("/start", user_id="123")
        server.send_message.assert_called_once()
        self.assertEqual(server.send_message.call_args.args[0], "main-token")
        self.assertEqual(server.send_message.call_args.args[1], 123)

    def test_main_webhook_message_created(self):
        server = self.import_server()
        client = server.app.test_client()

        response = client.post("/webhook", json={
            "update_type": "message_created",
            "message": {
                "recipient": {
                    "chat_id": 123
                },
                "sender": {
                    "user_id": 456
                },
                "body": {
                    "text": "контакты"
                }
            }
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})

        server.bot.get_response.assert_called_once_with("контакты", user_id="456")
        server.send_message.assert_called_once()
        self.assertEqual(server.send_message.call_args.args[0], "main-token")
        self.assertEqual(server.send_message.call_args.args[1], 123)

    def test_main_webhook_ignores_invalid_message(self):
        server = self.import_server()
        client = server.app.test_client()

        response = client.post("/webhook", json={
            "update_type": "message_created",
            "message": {}
        })

        self.assertEqual(response.status_code, 200)
        server.bot.get_response.assert_not_called()
        server.send_message.assert_not_called()

    def test_feedback_webhook_bot_started(self):
        server = self.import_server()
        client = server.app.test_client()

        response = client.post("/webhook/feedback", json={
            "update_type": "bot_started",
            "chat_id": 123
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})

        server.send_message.assert_called_once()
        self.assertEqual(server.send_message.call_args.args[0], "feedback-token")
        self.assertEqual(server.send_message.call_args.args[1], 123)
        self.assertIn("Здравствуйте", server.send_message.call_args.args[2])

    def test_feedback_webhook_course_list(self):
        server = self.import_server()
        client = server.app.test_client()

        with patch.object(server, "answer_or_send") as mock_answer_or_send:
            response = client.post("/webhook/feedback", json={
                "update_type": "message_callback",
                "callback": {
                    "chat_id": 123,
                    "callback_id": "cb-1",
                    "payload": "feedback:course_list",
                    "user": {
                        "user_id": 456
                    }
                }
            })

        self.assertEqual(response.status_code, 200)
        mock_answer_or_send.assert_called_once()
        self.assertEqual(mock_answer_or_send.call_args.args[0], "feedback-token")
        self.assertEqual(mock_answer_or_send.call_args.args[1], 123)
        self.assertEqual(mock_answer_or_send.call_args.args[2], "cb-1")
        self.assertIn("Выберите курс", mock_answer_or_send.call_args.args[3])

    def test_feedback_webhook_course_selected_success(self):
        server = self.import_server()
        client = server.app.test_client()
        server.feedback_bot.course_exists.return_value = True

        with patch.object(server, "answer_or_send") as mock_answer_or_send:
            response = client.post("/webhook/feedback", json={
                "update_type": "message_callback",
                "callback": {
                    "chat_id": 123,
                    "callback_id": "cb-1",
                    "payload": "feedback:course:Python",
                    "user": {
                        "user_id": 456
                    }
                }
            })

        self.assertEqual(response.status_code, 200)
        server.feedback_bot.set_course.assert_called_once_with("456", "Python")
        self.assertIn("Курс выбран: Python", mock_answer_or_send.call_args.args[3])

    def test_feedback_webhook_course_selected_not_found(self):
        server = self.import_server()
        client = server.app.test_client()
        server.feedback_bot.course_exists.return_value = False

        with patch.object(server, "answer_or_send") as mock_answer_or_send:
            response = client.post("/webhook/feedback", json={
                "update_type": "message_callback",
                "callback": {
                    "chat_id": 123,
                    "callback_id": "cb-1",
                    "payload": "feedback:course:Unknown",
                    "user": {
                        "user_id": 456
                    }
                }
            })

        self.assertEqual(response.status_code, 200)
        server.feedback_bot.set_course.assert_not_called()
        self.assertIn("Курс не найден", mock_answer_or_send.call_args.args[3])

    def test_feedback_webhook_lesson_selected_success(self):
        server = self.import_server()
        client = server.app.test_client()

        server.feedback_bot.get_state.return_value = {
            "course": "Python"
        }
        server.feedback_bot.lesson_exists.return_value = True

        with patch.object(server, "answer_or_send") as mock_answer_or_send:
            response = client.post("/webhook/feedback", json={
                "update_type": "message_callback",
                "callback": {
                    "chat_id": 123,
                    "callback_id": "cb-1",
                    "payload": "feedback:lesson:1",
                    "user": {
                        "user_id": 456
                    }
                }
            })

        self.assertEqual(response.status_code, 200)
        server.feedback_bot.set_lesson.assert_called_once_with("456", "1")
        self.assertIn("Урок: №1", mock_answer_or_send.call_args.args[3])

    def test_feedback_webhook_type_online(self):
        server = self.import_server()
        client = server.app.test_client()

        with patch.object(server, "answer_or_send") as mock_answer_or_send:
            response = client.post("/webhook/feedback", json={
                "update_type": "message_callback",
                "callback": {
                    "chat_id": 123,
                    "callback_id": "cb-1",
                    "payload": "feedback:type:online",
                    "user": {
                        "user_id": 456
                    }
                }
            })

        self.assertEqual(response.status_code, 200)
        server.feedback_bot.generate_feedback.assert_called_once_with("456", "online")
        self.assertEqual(mock_answer_or_send.call_args.args[3], "Текст обратной связи")

    def test_feedback_webhook_type_offline(self):
        server = self.import_server()
        client = server.app.test_client()

        with patch.object(server, "answer_or_send") as mock_answer_or_send:
            response = client.post("/webhook/feedback", json={
                "update_type": "message_callback",
                "callback": {
                    "chat_id": 123,
                    "callback_id": "cb-1",
                    "payload": "feedback:type:offline",
                    "user": {
                        "user_id": 456
                    }
                }
            })

        self.assertEqual(response.status_code, 200)
        server.feedback_bot.generate_feedback.assert_called_once_with("456", "offline")
        self.assertEqual(mock_answer_or_send.call_args.args[3], "Текст обратной связи")

    def test_feedback_webhook_unknown_command(self):
        server = self.import_server()
        client = server.app.test_client()

        with patch.object(server, "answer_or_send") as mock_answer_or_send:
            response = client.post("/webhook/feedback", json={
                "update_type": "message_callback",
                "callback": {
                    "chat_id": 123,
                    "callback_id": "cb-1",
                    "payload": "unknown",
                    "user": {
                        "user_id": 456
                    }
                }
            })

        self.assertEqual(response.status_code, 200)
        self.assertIn("Нажмите кнопку", mock_answer_or_send.call_args.args[3])

    def test_feedback_webhook_handles_exception_and_sends_error_message(self):
        server = self.import_server()
        client = server.app.test_client()

        with patch.object(server, "extract_feedback_event", side_effect=Exception("boom")):
            response = client.post("/webhook/feedback", json={
                "update_type": "message_callback",
                "chat_id": 123
            })

        self.assertEqual(response.status_code, 200)
        server.send_message.assert_not_called()

    def test_reminder_webhook_without_response(self):
        server = self.import_server()
        client = server.app.test_client()

        server.reminder_bot.handle_update.return_value = None

        response = client.post("/webhook/reminder", json={
            "update_type": "message_created"
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})
        server.reminder_bot.handle_update.assert_called_once()
        server.send_message.assert_not_called()

    def test_reminder_webhook_with_response(self):
        server = self.import_server()
        client = server.app.test_client()

        server.reminder_bot.handle_update.return_value = {
            "chat_id": 123,
            "callback_id": "cb-1",
            "text": "Ответ напоминалки",
            "attachments": [
                {
                    "type": "inline_keyboard",
                    "payload": {
                        "buttons": []
                    }
                }
            ]
        }

        with patch.object(server, "answer_or_send") as mock_answer_or_send:
            response = client.post("/webhook/reminder", json={
                "update_type": "message_created"
            })

        self.assertEqual(response.status_code, 200)
        mock_answer_or_send.assert_called_once()
        self.assertEqual(mock_answer_or_send.call_args.args[0], "reminder-token")
        self.assertEqual(mock_answer_or_send.call_args.args[1], 123)
        self.assertEqual(mock_answer_or_send.call_args.args[2], "cb-1")
        self.assertEqual(mock_answer_or_send.call_args.args[3], "Ответ напоминалки")

    def test_reminder_webhook_handles_exception(self):
        server = self.import_server()
        client = server.app.test_client()

        server.reminder_bot.handle_update.side_effect = Exception("boom")

        response = client.post("/webhook/reminder", json={
            "update_type": "message_created"
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
