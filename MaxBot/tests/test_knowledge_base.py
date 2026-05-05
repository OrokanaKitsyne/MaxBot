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

    def test_load_documents_does_not_crash(self):
        data = [
            {
                "type": "course_page",
                "title": "Геймдизайн",
                "text": "Курс по геймдизайну для детей 10-11 лет."
            },
            {
                "type": "course_page",
                "title": "Питон",
                "text": "Курс по Python для подростков."
            }
        ]

        path = self.create_temp_json(data)
        try:
            kb = LocalKnowledgeBase(path=path)

            self.assertIsInstance(kb.documents, list)
        finally:
            os.remove(path)

    def test_get_context_for_query_returns_string(self):
        data = [
            {
                "type": "course_page",
                "title": "Геймдизайн",
                "text": "Курс по геймдизайну для детей 10-11 лет."
            },
            {
                "type": "course_page",
                "title": "Питон",
                "text": "Курс по Python для подростков."
            }
        ]

        path = self.create_temp_json(data)
        try:
            kb = LocalKnowledgeBase(path=path)
            context = kb.get_context_for_query(
                "геймдизайн",
                top_k=1,
                max_chars=500
            )

            self.assertIsInstance(context, str)
        finally:
            os.remove(path)

    def test_get_context_for_query_with_empty_base_returns_string(self):
        path = self.create_temp_json([])
        try:
            kb = LocalKnowledgeBase(path=path)
            context = kb.get_context_for_query(
                "геймдизайн",
                top_k=1,
                max_chars=500
            )

            self.assertIsInstance(context, str)
            self.assertEqual(context, "")
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

            self.assertIsInstance(kb.documents, list)
            self.assertEqual(kb.documents, [])
        finally:
            os.remove(temp.name)


if __name__ == "__main__":
    unittest.main()
