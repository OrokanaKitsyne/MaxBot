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
                "Я могу рассказать о курсах, формате обучения и помочь с выбором.\n"
                "Просто напишите ваш вопрос."
            )

        if lowered == "контакты":
            return "Напишите ваш блок с контактами."

        return self.ai.ask(text)
