import unittest
from unittest.mock import patch

from ai_module import AIService


class TestAIService(unittest.TestCase):
    @patch.dict("os.environ", {"GROQ_API_KEY": "fake-key"})
    @patch("ai_module.Groq")
    @patch("ai_module.LocalKnowledgeBase")
    @patch("ai_module.LocalKnowledge")
    def test_is_location_question(self, mock_loc, mock_kb, mock_groq):
        service = AIService()

        self.assertTrue(service.is_location_question("Где проходят занятия?"))
        self.assertTrue(service.is_location_question("Покажи адреса площадок"))
        self.assertFalse(service.is_location_question("Какие есть курсы?"))


if __name__ == "__main__":
    unittest.main()
