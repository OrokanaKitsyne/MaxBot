from ai_module import AIService


class BotLogic:
    def __init__(self):
        self.ai = AIService()

    def get_start_text(self) -> str:
        return (
            "Привет! Я бот-консультант.\n\n"
            "Я могу рассказать об обучении, курсах и ответить на ваши вопросы.\n"
            "Выберите кнопку ниже или напишите сообщение."
        )

    def get_courses_text(self) -> str:
        return (
            "Факультет программирования:\n"
            "7-9 лет — Компьютерная грамотность\n"
            "9-10 лет — Визуальное программирование\n"
            "9-14 лет — Видеоблогинг\n"
            "9-14 лет — Графический дизайн\n"
            "10-11 лет — Геймдизайн\n"
            "11-13 лет — Создание веб-сайтов\n"
            "12-16 лет — Разработка игр на Юнити\n"
            "14-17 лет — Питон Про\n"
            "15-18 лет — Веб-разработка\n\n"
            "Факультет математики:\n"
            "6-8 лет — Математика+\n"
            "9-13 лет — Математика+"
        )

    def get_contacts_text(self) -> str:
        return (
            "Телефон: +79200690200\n"
            "Email: nn@algoritmika.org\n"
            "Официальный сайт: https://algoritmika.org/ru"
        )

    def get_help_text(self) -> str:
        return (
            "Я помогу подобрать подходящий курс для ребёнка 👩‍💻\n\n"
            "Вы можете:\n"
            "• посмотреть список курсов\n"
            "• узнать подробности обучения\n"
            "• задать любой вопрос\n"
            "• получить контакты для записи\n\n"
            "Напишите, что вас интересует, и я подскажу 🙂"
        )

    def get_response(self, text: str) -> str:
        text = (text or "").strip()
        lowered = text.lower()

        if lowered == "/start":
            return self.get_start_text()

        if lowered == "список курсов":
            return self.get_courses_text()

        if lowered == "контакты":
            return self.get_contacts_text()

        if lowered == "помощь":
            return self.get_help_text()

        return self.ai.ask(text)
