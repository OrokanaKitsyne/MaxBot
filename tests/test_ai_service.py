import os
import unittest
from unittest.mock import MagicMock, patch

import MaxBot.ai_module as ai_module


class TestAIService(unittest.TestCase):
    @patch.dict(os.environ, {"GROQ_API_KEY": "fake-key"})
    def test_is_location_question(self):
        with patch.object(ai_module, "Groq"), \
             patch.object(ai_module, "LocalKnowledgeBase"), \
             patch.object(ai_module, "LocalKnowledge"):

            service = ai_module.AIService()

            self.assertTrue(service.is_location_question("Где проходят занятия?"))
            self.assertTrue(service.is_location_question("Покажи адреса площадок"))
            self.assertTrue(service.is_location_question("Какие есть места для обучения?"))
            self.assertFalse(service.is_location_question("Какие есть курсы?"))

    @patch.dict(os.environ, {"GROQ_API_KEY": "fake-key"})
    def test_empty_question(self):
        with patch.object(ai_module, "Groq"), \
             patch.object(ai_module, "LocalKnowledgeBase"), \
             patch.object(ai_module, "LocalKnowledge"):

            service = ai_module.AIService()
            result = service.ask("")

            self.assertEqual(result, "Пожалуйста, напишите вопрос.")

    @patch.dict(os.environ, {"GROQ_API_KEY": "fake-key"})
    def test_location_question_returns_locations_directly(self):
        mock_loc_instance = MagicMock()
        mock_loc_instance.get_locations_text.return_value = "Вот наши площадки в Нижнем Новгороде..."

        with patch.object(ai_module, "Groq"), \
             patch.object(ai_module, "LocalKnowledgeBase"), \
             patch.object(ai_module, "LocalKnowledge", return_value=mock_loc_instance):

            service = ai_module.AIService()
            result = service.ask("Где проходят занятия?")

            self.assertEqual(result, "Вот наши площадки в Нижнем Новгороде...")
            mock_loc_instance.get_locations_text.assert_called_once()

    @patch.dict(os.environ, {"GROQ_API_KEY": "fake-key"})
    def test_fallback_when_no_context(self):
        mock_kb_instance = MagicMock()
        mock_kb_instance.get_context_for_query.return_value = ""

        with patch.object(ai_module, "Groq"), \
             patch.object(ai_module, "LocalKnowledgeBase", return_value=mock_kb_instance), \
             patch.object(ai_module, "LocalKnowledge"):

            service = ai_module.AIService()
            result = service.ask("Расскажи что-нибудь редкое")

            self.assertIn("Я не нашёл точной информации", result)
            self.assertIn("Телефон", result)

    @patch.dict(os.environ, {"GROQ_API_KEY": "fake-key"})
    def test_answer_from_ai(self):
        mock_kb_instance = MagicMock()
        mock_kb_instance.get_context_for_query.return_value = "Курс по Python для подростков."

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "У нас есть курс по Python для подростков."

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch.object(ai_module, "Groq", return_value=mock_client), \
             patch.object(ai_module, "LocalKnowledgeBase", return_value=mock_kb_instance), \
             patch.object(ai_module, "LocalKnowledge"):

            service = ai_module.AIService()
            result = service.ask("Какие есть курсы по Python?")

            self.assertIn("Python", result)

    @patch.dict(os.environ, {"GROQ_API_KEY": "fake-key"})
    def test_fallback_when_ai_returns_empty(self):
        mock_kb_instance = MagicMock()
        mock_kb_instance.get_context_for_query.return_value = "Какой-то контекст"

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = ""

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch.object(ai_module, "Groq", return_value=mock_client), \
             patch.object(ai_module, "LocalKnowledgeBase", return_value=mock_kb_instance), \
             patch.object(ai_module, "LocalKnowledge"):

            service = ai_module.AIService()
            result = service.ask("Любой вопрос")

            self.assertIn("Я не нашёл точной информации", result)

    @patch.dict(os.environ, {"GROQ_API_KEY": "fake-key"})
    def test_fallback_when_ai_raises_error(self):
        mock_kb_instance = MagicMock()
        mock_kb_instance.get_context_for_query.return_value = "Какой-то контекст"

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API error")

        with patch.object(ai_module, "Groq", return_value=mock_client), \
             patch.object(ai_module, "LocalKnowledgeBase", return_value=mock_kb_instance), \
             patch.object(ai_module, "LocalKnowledge"):

            service = ai_module.AIService()
            result = service.ask("Любой вопрос")

            self.assertIn("Я не нашёл точной информации", result)

    @patch.dict(os.environ, {"GROQ_API_KEY": "fake-key"})
    def test_cache_works(self):
        mock_kb_instance = MagicMock()
        mock_kb_instance.get_context_for_query.return_value = "Контекст про курсы"

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Ответ про курсы"

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch.object(ai_module, "Groq", return_value=mock_client), \
             patch.object(ai_module, "LocalKnowledgeBase", return_value=mock_kb_instance), \
             patch.object(ai_module, "LocalKnowledge"):

            service = ai_module.AIService()

            result1 = service.ask("Какие есть курсы?")
            result2 = service.ask("Какие есть курсы?")

            self.assertEqual(result1, result2)
            mock_client.chat.completions.create.assert_called_once()


if __name__ == "__main__":
    unittest.main()
