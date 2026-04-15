import json
import os
import tempfile
import unittest

from knowledge import LocalKnowledge


class TestLocalKnowledge(unittest.TestCase):
    def test_get_locations_returns_locations(self):
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

        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".json") as f:
            json.dump(data, f, ensure_ascii=False)
            temp_path = f.name

        try:
            kl = LocalKnowledge(path=temp_path)
            locations = kl.get_locations()

            self.assertEqual(len(locations), 1)
            self.assertEqual(locations[0]["name"], "Горная 56а")
        finally:
            os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()
