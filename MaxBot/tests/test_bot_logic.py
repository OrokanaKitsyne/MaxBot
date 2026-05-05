import unittest
from unittest.mock import MagicMock, patch


class TestBotLogic(unittest.TestCase):
    def create_bot(self):
        with patch("bot_logic.AIService") as mock_ai_cls:
            from bot_logic import BotLogic

            mock_ai = MagicMock()
            mock_ai.ask.return_value = "Ответ от AI"
            mock_ai_cls.return_value = mock_ai

            bot = BotLogic()
            bot.ai = mock_ai

            return bot, mock_ai

    def test_get_start_text_contains_greeting(self):
        bot, _ = self.create_bot()

        text = bot.get_start_text()

        self.assertIn("Привет", text)
        self.assertIn("бот-консультант", text)
        self.assertIn("Алгоритмики", text)

    def test_get_courses_text_contains_courses(self):
        bot, _ = self.create_bot()

        text = bot.get_courses_text()

        self.assertIn("Вот список курсов", text)
        self.assertIn("Факультет программирования", text)
        self.assertIn("Питон", text)
        self.assertIn("Математика", text)

    def test_get_contacts_text_contains_contacts(self):
        bot, _ = self.create_bot()

        text = bot.get_contacts_text()

        self.assertIn("+7 (920) 069-02-00", text)
        self.assertIn("nn@algoritmika.org", text)
        self.assertIn("algoritmika.org", text)

    def test_get_help_text_contains_available_actions(self):
        bot, _ = self.create_bot()

        text = bot.get_help_text()

        self.assertIn("список курсов", text)
        self.assertIn("места обучения", text)
        self.assertIn("оставить заявку", text)
        self.assertIn("контакты", text)

    def test_normalize_phone_valid_formats(self):
        bot, _ = self.create_bot()

        cases = {
            "+7 999 123-45-67": "+79991234567",
            "8 999 123 45 67": "+79991234567",
            "89991234567": "+79991234567",
            "79991234567": "+79991234567",
            "9991234567": "+79991234567",
            "+79991234567": "+79991234567",
        }

        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(bot.normalize_phone(source), expected)

    def test_normalize_phone_invalid_formats(self):
        bot, _ = self.create_bot()

        invalid_phones = [
            "",
            None,
            "123",
            "999999999999999",
            "+1 999 123 45 67",
            "abcdef",
        ]

        for phone in invalid_phones:
            with self.subTest(phone=phone):
                self.assertIsNone(bot.normalize_phone(phone))

    def test_is_valid_email(self):
        bot, _ = self.create_bot()

        self.assertTrue(bot.is_valid_email("test@mail.ru"))
        self.assertTrue(bot.is_valid_email("user.name@example.com"))

        self.assertFalse(bot.is_valid_email("test"))
        self.assertFalse(bot.is_valid_email("test@"))
        self.assertFalse(bot.is_valid_email("@mail.ru"))
        self.assertFalse(bot.is_valid_email("test@mail"))

    def test_get_response_empty_message(self):
        bot, _ = self.create_bot()

        response = bot.get_response("")

        self.assertEqual(response, "Пожалуйста, напишите сообщение 😊")

    def test_get_response_start_command(self):
        bot, _ = self.create_bot()

        response = bot.get_response("/start")

        self.assertIn("Привет", response)
        self.assertIn("бот-консультант", response)

    def test_get_response_courses_command(self):
        bot, _ = self.create_bot()

        response = bot.get_response("список курсов")

        self.assertIn("Вот список курсов", response)
        self.assertIn("Питон", response)

    def test_get_response_contacts_command(self):
        bot, _ = self.create_bot()

        response = bot.get_response("контакты")

        self.assertIn("Телефон", response)
        self.assertIn("Email", response)

    def test_get_response_help_command(self):
        bot, _ = self.create_bot()

        response = bot.get_response("помощь")

        self.assertIn("Я помогу", response)
        self.assertIn("Записаться", response)

    def test_get_response_email_without_application(self):
        bot, _ = self.create_bot()

        response = bot.get_response("client@mail.ru")

        self.assertIn("Похоже, вы отправили email", response)
        self.assertIn("Записаться", response)

    def test_get_response_unknown_message_calls_ai(self):
        bot, mock_ai = self.create_bot()

        response = bot.get_response("Расскажи про Python")

        self.assertEqual(response, "Ответ от AI")
        mock_ai.ask.assert_called_once_with("Расскажи про Python")

    def test_start_application_sets_state(self):
        bot, _ = self.create_bot()

        response = bot.start_application("user-1")

        self.assertIn("Как вас зовут", response)
        self.assertIn("user-1", bot.user_states)
        self.assertEqual(bot.user_states["user-1"]["step"], "name")

    def test_application_name_too_short(self):
        bot, _ = self.create_bot()
        bot.start_application("user-1")

        response = bot.process_application_step("user-1", "A")

        self.assertIn("напишите ваше имя", response)
        self.assertEqual(bot.user_states["user-1"]["step"], "name")

    def test_application_valid_name_moves_to_phone(self):
        bot, _ = self.create_bot()
        bot.start_application("user-1")

        response = bot.process_application_step("user-1", "Иван")

        self.assertIn("номер телефона", response)
        self.assertEqual(bot.user_states["user-1"]["step"], "phone")
        self.assertEqual(bot.user_states["user-1"]["data"]["name"], "Иван")

    def test_application_invalid_phone_keeps_phone_step(self):
        bot, _ = self.create_bot()
        bot.start_application("user-1")
        bot.process_application_step("user-1", "Иван")

        response = bot.process_application_step("user-1", "123")

        self.assertIn("номер телефона введён некорректно", response)
        self.assertEqual(bot.user_states["user-1"]["step"], "phone")

    def test_application_valid_phone_moves_to_email(self):
        bot, _ = self.create_bot()
        bot.start_application("user-1")
        bot.process_application_step("user-1", "Иван")

        response = bot.process_application_step("user-1", "89991234567")

        self.assertIn("Номер сохранён", response)
        self.assertEqual(bot.user_states["user-1"]["step"], "email")
        self.assertEqual(bot.user_states["user-1"]["data"]["phone"], "+79991234567")

    def test_application_invalid_email_keeps_email_step(self):
        bot, _ = self.create_bot()
        bot.start_application("user-1")
        bot.process_application_step("user-1", "Иван")
        bot.process_application_step("user-1", "89991234567")

        response = bot.process_application_step("user-1", "bad-email")

        self.assertIn("email введён некорректно", response)
        self.assertEqual(bot.user_states["user-1"]["step"], "email")

    def test_application_success_removes_state(self):
        bot, _ = self.create_bot()
        bot.start_application("user-1")
        bot.process_application_step("user-1", "Иван")
        bot.process_application_step("user-1", "89991234567")

        with patch.object(bot, "send_application_to_google_sheets", return_value=True) as mock_send:
            response = bot.process_application_step("user-1", "ivan@mail.ru")

        self.assertIn("Заявка отправлена", response)
        self.assertNotIn("user-1", bot.user_states)
        mock_send.assert_called_once()

    def test_application_failed_sending_removes_state_and_returns_contacts(self):
        bot, _ = self.create_bot()
        bot.start_application("user-1")
        bot.process_application_step("user-1", "Иван")
        bot.process_application_step("user-1", "89991234567")

        with patch.object(bot, "send_application_to_google_sheets", return_value=False):
            response = bot.process_application_step("user-1", "ivan@mail.ru")

        self.assertIn("Заявку не удалось отправить", response)
        self.assertIn("+7 (920) 069-02-00", response)
        self.assertNotIn("user-1", bot.user_states)

    def test_process_application_step_without_state_returns_empty_string(self):
        bot, _ = self.create_bot()

        response = bot.process_application_step("unknown-user", "Иван")

        self.assertEqual(response, "")

    def test_send_application_to_google_sheets_without_url_returns_false(self):
        bot, _ = self.create_bot()
        bot.google_script_url = ""

        result = bot.send_application_to_google_sheets({
            "name": "Иван",
            "phone": "+79991234567",
            "email": "ivan@mail.ru",
            "user_id": "1",
            "chat_id": "1"
        })

        self.assertFalse(result)

    @patch("bot_logic.requests.post")
    def test_send_application_to_google_sheets_success(self, mock_post):
        bot, _ = self.create_bot()
        bot.google_script_url = "https://example.com/script"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "ok"
        mock_post.return_value = mock_response

        result = bot.send_application_to_google_sheets({
            "name": "Иван",
            "phone": "+79991234567",
            "email": "ivan@mail.ru",
            "user_id": "1",
            "chat_id": "1"
        })

        self.assertTrue(result)
        mock_post.assert_called_once()

    @patch("bot_logic.requests.post")
    def test_send_application_to_google_sheets_error_returns_false(self, mock_post):
        bot, _ = self.create_bot()
        bot.google_script_url = "https://example.com/script"

        mock_post.side_effect = Exception("network error")

        result = bot.send_application_to_google_sheets({
            "name": "Иван",
            "phone": "+79991234567",
            "email": "ivan@mail.ru",
            "user_id": "1",
            "chat_id": "1"
        })

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
