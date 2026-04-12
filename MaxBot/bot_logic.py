from ai_module import AIService


class BotLogic:
    def __init__(self):
        self.ai = AIService()

    def get_response(self, text: str) -> str:
        text = (text or "").strip()
        lowered = text.lower()

        if lowered == "/start":
            return (
                "Привет! Я бот-помощник.\n\n"
                "Я могу отвечать на вопросы по информации с сайта.\n"
                "Напишите ваш вопрос."
            )

        return self.ai.ask(text)
