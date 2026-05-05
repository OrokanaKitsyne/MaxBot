import unittest
from unittest.mock import MagicMock, patch


class TestAIService(unittest.TestCase):
    @patch.dict("os.environ", {"GROQ_API_KEY": "fake-key"})
    @patch("ai_module.Groq")
    @patch("ai_module.LocalKnowledgeBase")
    @patch("ai_module.LocalKnowledge")
    def test_is_location_question(self, mock_loc, mock_kb, mock_groq):
        from ai_module import AIService

        service = AIService()

        self.assertTrue(service.is_location_question("Где проходят занятия?"))
        self.assertTrue(service.is_location_question("Покажи адреса площадок"))
        self.assertTrue(service.is_location_question("Какие есть места для обучения?"))
        self.assertFalse(service.is_location_question("Какие есть курсы?"))

    @patch.dict("os.environ", {"GROQ_API_KEY": "fake-key"})
    @patch("ai_module.Groq")
    @patch("ai_module.LocalKnowledgeBase")
    @patch("ai_module.LocalKnowledge")
    def test_empty_question(self, mock_loc, mock_kb, mock_groq):
        from ai_module import AIService

        service = AIService()
        result = service.ask("")

        self.assertEqual(result, "Пожалуйста, напишите свой вопрос 😊")

    @patch.dict("os.environ", {"GROQ_API_KEY": "fake-key"})
    @patch("ai_module.Groq")
    @patch("ai_module.LocalKnowledgeBase")
    @patch("ai_module.LocalKnowledge")
    def test_location_question_returns_locations_directly(self, mock_loc_cls, mock_kb_cls, mock_groq):
        from ai_module import AIService

        mock_loc = MagicMock()
        mock_loc.get_locations_text.return_value = "Вот наши площадки в Нижнем Новгороде..."
        mock_loc_cls.return_value = mock_loc

        service = AIService()
        result = service.ask("Где проходят занятия?")

        self.assertEqual(result, "Вот наши площадки в Нижнем Новгороде...")
        mock_loc.get_locations_text.assert_called_once()

    @patch.dict("os.environ", {"GROQ_API_KEY": "fake-key"})
    @patch("ai_module.Groq")
    @patch("ai_module.LocalKnowledgeBase")
    @patch("ai_module.LocalKnowledge")
    def test_fallback_when_no_context(self, mock_loc_cls, mock_kb_cls, mock_groq_cls):
        from ai_module import AIService

        mock_kb = MagicMock()
        mock_kb.get_context_for_query.return_value = ""
        mock_kb_cls.return_value = mock_kb

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = ""

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_cls.return_value = mock_client

        service = AIService()
        result = service.ask("Расскажи что-нибудь редкое")

        self.assertIn("Я не нашёл точной информации", result)

    @patch.dict("os.environ", {"GROQ_API_KEY": "fake-key"})
    @patch("ai_module.Groq")
    @patch("ai_module.LocalKnowledgeBase")
    @patch("ai_module.LocalKnowledge")
    def test_answer_from_ai(self, mock_loc_cls, mock_kb_cls, mock_groq_cls):
        from ai_module import AIService

        mock_kb = MagicMock()
        mock_kb.get_context_for_query.return_value = "Курс по Python для подростков."
        mock_kb_cls.return_value = mock_kb

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "У нас есть курс по Python для подростков."

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_cls.return_value = mock_client

        service = AIService()
        result = service.ask("Какие есть курсы по Python?")

        self.assertIn("курс по Python", result)

    @patch.dict("os.environ", {"GROQ_API_KEY": "fake-key"})
    @patch("ai_module.Groq")
    @patch("ai_module.LocalKnowledgeBase")
    @patch("ai_module.LocalKnowledge")
    def test_fallback_when_ai_returns_empty(self, mock_loc_cls, mock_kb_cls, mock_groq_cls):
        from ai_module import AIService

        mock_kb = MagicMock()
        mock_kb.get_context_for_query.return_value = "Какой-то контекст"
        mock_kb_cls.return_value = mock_kb

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = ""

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_cls.return_value = mock_client

        service = AIService()
        result = service.ask("Любой вопрос")

        self.assertIn("Я не нашёл точной информации", result)

    @patch.dict("os.environ", {"GROQ_API_KEY": "fake-key"})
    @patch("ai_module.Groq")
    @patch("ai_module.LocalKnowledgeBase")
    @patch("ai_module.LocalKnowledge")
    def test_fallback_when_ai_raises_error(self, mock_loc_cls, mock_kb_cls, mock_groq_cls):
        from ai_module import AIService

        mock_kb = MagicMock()
        mock_kb.get_context_for_query.return_value = "Какой-то контекст"
        mock_kb_cls.return_value = mock_kb

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API error")
        mock_groq_cls.return_value = mock_client

        service = AIService()
        result = service.ask("Любой вопрос")

        self.assertIn("Я не нашёл точной информации", result)

    @patch.dict("os.environ", {"GROQ_API_KEY": "fake-key"})
    @patch("ai_module.Groq")
    @patch("ai_module.LocalKnowledgeBase")
    @patch("ai_module.LocalKnowledge")
    def test_cache_works(self, mock_loc_cls, mock_kb_cls, mock_groq_cls):
        from ai_module import AIService

        mock_kb = MagicMock()
        mock_kb.get_context_for_query.return_value = "Контекст про курсы"
        mock_kb_cls.return_value = mock_kb

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Ответ про курсы"

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_cls.return_value = mock_client

        service = AIService()

        result1 = service.ask("Какие есть курсы?")
        result2 = service.ask("Какие есть курсы?")

        self.assertEqual(result1, result2)
        mock_client.chat.completions.create.assert_called_once()


if __name__ == "__main__":
    unittest.main()
