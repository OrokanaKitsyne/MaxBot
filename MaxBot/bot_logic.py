class BotLogic:
    def get_response(self, text):
        text = text.lower()

        if text == "/start":
            return (
                "Привет! 👋\n\n"
                "Я бот Алгоритмики.\n"
                "Напиши:\n"
                "- курсы\n"
                "- контакты"
            )

        elif text == "курсы":
            return (
                "Доступные направления:\n"
                "- Python\n"
                "- Веб\n"
                "- Unity\n\n"
                "Напиши название курса"
            )

        elif text == "контакты":
            return (
                "Контакты:\n"
                "+7 (920) 069-02-00\n"
                "nn@algoritmika.org"
            )

        elif "python" in text:
            return "Курс Python 🚀\nhttps://nn.algoritmika.org"

        elif "веб" in text:
            return "Курс веб-разработки 🌐\nhttps://nn.algoritmika.org"

        else:
            return "Я пока понимаю: /start, курсы, контакты"