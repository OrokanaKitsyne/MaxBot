import json
import os
import tempfile
import unittest

from knowledge_base import LocalKnowledgeBase


class TestLocalKnowledgeBase(unittest.TestCase):
    def create_temp_json(self, data):
        temp = tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            encoding="utf-8",
            suffix=".json"
        )
        json.dump(data, temp, ensure_ascii=False, indent=2)
        temp.close()
        return temp.name

    def test_load_documents_from_full_text_sections_and_courses(self):
        data = {
            "full_text": "Общая информация о школе Алгоритмика.",
            "sections": [
                {
                    "raw_text": "Секция с информацией о расписании занятий."
                },
                {
                    "raw_text": "Секция с информацией о площадках обучения."
                }
            ],
            "courses": [
                {
                    "raw_text": "Курс Геймдизайн для детей 10-11 лет."
                },
                {
                    "raw_text": "Курс Python для подростков."
                }
            ]
        }

        path = self.create_temp_json(data)
        try:
            kb = LocalKnowledgeBase(path=path)

            self.assertEqual(len(kb.documents), 5)
            self.assertIn("Общая информация о школе Алгоритмика.", kb.documents)
            self.assertIn("Курс Геймдизайн для детей 10-11 лет.", kb.documents)
            self.assertIn("Курс Python для подростков.", kb.documents)
        finally:
            os.remove(path)

    def test_get_context_for_query_returns_relevant_text(self):
        data = {
            "full_text": "Общая информация о школе Алгоритмика.",
            "sections": [
                {
                    "raw_text": "Занятия проходят на площадках в Нижнем Новгороде."
                }
            ],
            "courses": [
                {
                    "raw_text": "Курс Геймдизайн для детей 10-11 лет."
                },
                {
                    "raw_text": "Курс Python для подростков."
                }
            ]
        }

        path = self.create_temp_json(data)
        try:
            kb = LocalKnowledgeBase(path=path)
            context = kb.get_context_for_query(
                "геймдизайн",
                top_k=1,
                max_chars=500
            )

            self.assertIsInstance(context, str)
            self.assertIn("Геймдизайн", context)
            self.assertNotIn("Python", context)
        finally:
            os.remove(path)

    def test_get_context_for_query_respects_top_k(self):
        data = {
            "sections": [
                {
                    "raw_text": "Геймдизайн: первое совпадение."
                },
                {
                    "raw_text": "Геймдизайн: второе совпадение."
                },
                {
                    "raw_text": "Геймдизайн: третье совпадение."
                }
            ]
        }

        path = self.create_temp_json(data)
        try:
            kb = LocalKnowledgeBase(path=path)
            context = kb.get_context_for_query(
                "геймдизайн",
                top_k=2,
                max_chars=1000
            )

            self.assertIn("первое совпадение", context)
            self.assertIn("второе совпадение", context)
            self.assertNotIn("третье совпадение", context)
        finally:
            os.remove(path)

    def test_get_context_for_query_respects_max_chars(self):
        data = {
            "full_text": "Геймдизайн " + ("очень длинный текст " * 50)
        }

        path = self.create_temp_json(data)
        try:
            kb = LocalKnowledgeBase(path=path)
            context = kb.get_context_for_query(
                "геймдизайн",
                top_k=1,
                max_chars=30
            )

            self.assertLessEqual(len(context), 30)
        finally:
            os.remove(path)

    def test_get_context_for_query_returns_empty_string_when_no_match(self):
        data = {
            "full_text": "Информация только про Python."
        }

        path = self.create_temp_json(data)
        try:
            kb = LocalKnowledgeBase(path=path)
            context = kb.get_context_for_query(
                "геймдизайн",
                top_k=1,
                max_chars=500
            )

            self.assertEqual(context, "")
        finally:
            os.remove(path)

    def test_get_context_for_query_returns_empty_string_when_query_empty(self):
        data = {
            "full_text": "Курс Геймдизайн для детей 10-11 лет."
        }

        path = self.create_temp_json(data)
        try:
            kb = LocalKnowledgeBase(path=path)
            context = kb.get_context_for_query(
                "",
                top_k=1,
                max_chars=500
            )

            self.assertEqual(context, "")
        finally:
            os.remove(path)

    def test_list_json_is_ignored(self):
        data = [
            {
                "type": "course_page",
                "title": "Геймдизайн",
                "text": "Курс по геймдизайну для детей 10-11 лет."
            }
        ]

        path = self.create_temp_json(data)
        try:
            kb = LocalKnowledgeBase(path=path)

            self.assertEqual(kb.documents, [])
        finally:
            os.remove(path)

    def test_invalid_json_does_not_crash(self):
        temp = tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            encoding="utf-8",
            suffix=".json"
        )
        temp.write("{ broken json }")
        temp.close()

        try:
            kb = LocalKnowledgeBase(path=temp.name)

            self.assertEqual(kb.documents, [])
        finally:
            os.remove(temp.name)


if __name__ == "__main__":
    unittest.main()
