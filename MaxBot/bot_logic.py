from ai_module import AIService


class BotLogic:
    def __init__(self):
        self.ai = AIService()

    def get_response(self, text: str) -> str:
        text = (text or "").strip()
        lowered = text.lower()

        if lowered == "/start":
            return (
                "Привет! Я бот-помощник по алгоритмике.\n\n"
                "Я могу объяснять темы по алгоритмам и отвечать на вопросы.\n"
                "Просто напишите ваш вопрос."
            )

        if lowered == "контакты":
            return "Контакты: example@mail.com"

        if lowered == "помощь":
            return (
                "Примеры вопросов:\n"
                "- что такое бинарный поиск\n"
                "- объясни сортировку пузырьком\n"
                "- как работает алгоритм дейкстры"
            )

        return self.ai.ask(text)
