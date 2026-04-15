import json
import os
import tempfile
import unittest

from knowledge import LocalKnowledge


class TestLocalKnowledge(unittest.TestCase):
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

    def test_get_locations_returns_list(self):
        data = [
            {
                "city": "Нижний Новгород",
                "locations": [
                    {
                        "name": "Горная 56а",
                        "district": "Приокский район",
                        "short_address": "ул. Горная 56а, каб. 24",
                        "full_address": "603032, Нижний Новгород, ул. Горная 56а, каб. 24",
                        "phone": "+7 (920) 069-02-00"
                    }
                ]
            }
        ]

        path = self.create_temp_json(data)
        try:
            kl = LocalKnowledge(path=path)
            locations = kl.get_locations()

            self.assertEqual(len(locations), 1)
            self.assertEqual(locations[0]["name"], "Горная 56а")
            self.assertEqual(locations[0]["district"], "Приокский район")
        finally:
            os.remove(path)

    def test_get_locations_text_contains_data(self):
        data = [
            {
                "city": "Нижний Новгород",
                "locations": [
                    {
                        "name": "Ванеева 133",
                        "district": "Советский район",
                        "short_address": "ул. Ванеева 133, каб. 8",
                        "full_address": "г. Н.Новгород, ул. Ванеева 133: литер А1, этаж 2, кабинет 8",
                        "phone": "+7 (920) 069-02-00"
                    }
                ]
            }
        ]

        path = self.create_temp_json(data)
        try:
            kl = LocalKnowledge(path=path)
            text = kl.get_locations_text()

            self.assertIn("Вот наши площадки", text)
            self.assertIn("Ванеева 133", text)
            self.assertIn("Советский район", text)
            self.assertIn("+7 (920) 069-02-00", text)
        finally:
            os.remove(path)

    def test_get_locations_text_when_no_data(self):
        path = self.create_temp_json([])
        try:
            kl = LocalKnowledge(path=path)
            text = kl.get_locations_text()

            self.assertEqual(text, "Информация о площадках временно недоступна.")
        finally:
            os.remove(path)

    def test_invalid_json_does_not_crash(self):
        temp = tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            encoding="utf-8",
            suffix=".json"
        )
        temp.write("{ invalid json }")
        temp.close()

        try:
            kl = LocalKnowledge(path=temp.name)
            self.assertEqual(kl.documents, [])
        finally:
            os.remove(temp.name)


if __name__ == "__main__":
    unittest.main()
