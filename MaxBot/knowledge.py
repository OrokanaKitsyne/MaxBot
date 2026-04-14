import json


class LocalKnowledge:
    def __init__(self, path="knowledge.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.documents = json.load(f)
        except Exception as e:
            print("Ошибка загрузки knowledge.json:", e)
            self.documents = []

    def get_locations(self):
        if not self.documents:
            return []

        return self.documents[0].get("locations", [])

    def get_locations_text(self):
        locations = self.get_locations()

        if not locations:
            return "Информация о площадках временно недоступна."

        result = "Вот наши площадки в Нижнем Новгороде:\n\n"

        for loc in locations:
            result += f"{loc['name']} ({loc['district']})\n"
            result += f"{loc['short_address']}\n"

            if loc.get("phone"):
                result += f"{loc['phone']}\n"

            result += "\n"

        return result
