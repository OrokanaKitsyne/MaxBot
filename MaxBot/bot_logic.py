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
                "Я могу:\n"
                "- объяснять темы по алгоритмам;\n"
                "- помогать с задачами;\n"
                "- отвечать на учебные вопросы.\n\n"
                "Просто напиши свой вопрос."
            )

        if lowered == "контакты":
            return "Контакты: example@mail.com"

        if lowered == "помощь":
            return (
                "Напиши вопрос по алгоритмам, например:\n"
                "- что такое бинарный поиск\n"
                "- объясни графы\n"
                "- как работает сортировка слиянием"
            )

        return self.ai.ask(text)
