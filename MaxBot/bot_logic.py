class BotLogic:
    def __init__(self, api):
        self.api = api

    def handle_update(self, update):
        try:
            update_type = update.get("update_type")

            if update_type != "message_created":
                return

            message = update.get("message", {})
            text = message.get("body", {}).get("text", "").strip().lower()
            chat_id = message.get("chat_id")

            if not chat_id:
                print("Не найден chat_id")
                return

            print(f"Получено сообщение: {text}")

            response_text = self.get_response(text)
            self.api.send_message(chat_id, response_text)

        except Exception as e:
            print(f"Ошибка при обработке update: {e}")

    def get_response(self, text):
        if text == "/start":
            return (
                "Привет! Я бот Алгоритмики.\n\n"
                "Я умею:\n"
                "- показать курсы\n"
                "- дать контакты\n\n"
                "Напиши: курсы или контакты"
            )

        elif text == "курсы":
            return (
                "Доступные направления:\n"
                "- Python\n"
                "- Веб-разработка\n"
                "- Геймдизайн\n"
                "- Unity\n\n"
                "Напиши название курса, например: python"
            )

        elif text == "контакты":
            return (
                "Контакты:\n"
                "Телефон: +7 (920) 069-02-00\n"
                "Email: nn@algoritmika.org\n"
                "Сайт: https://nn.algoritmika.org"
            )

        elif text == "python":
            return (
                "Курс Python:\n"
                "Подходит для изучения программирования и создания собственных проектов.\n"
                "Подробнее: https://nn.algoritmika.org"
            )

        elif text == "веб":
            return (
                "Курс Веб-разработки:\n"
                "Изучение создания сайтов и основ web-технологий.\n"
                "Подробнее: https://nn.algoritmika.org"
            )

        else:
            return (
                "Я пока понимаю команды:\n"
                "/start\n"
                "курсы\n"
                "контакты\n"
                "python\n"
                "веб"
            )