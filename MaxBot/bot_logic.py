from ai_module import AIService


class BotLogic:
    def __init__(self):
        self.ai = AIService()

    def get_response(self, text: str) -> str:
        text = (text or "").strip()
        lowered = text.lower()

        if lowered == "/start":
            return (
                "Привет! Я бот-консультант Алгоритмики.\n\n"
                "Я могу помочь подобрать курс, рассказать про возраст, формат обучения и контакты.\n"
                "Напишите ваш вопрос."
            )

        return self.ai.ask(text)
