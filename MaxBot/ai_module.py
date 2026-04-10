from ollamafreeapi import OllamaFreeAPI


class AIService:
    def __init__(self):
        self.client = OllamaFreeAPI()

    def ask(self, text: str) -> str:
        text = (text or "").strip()

        if not text:
            return "Пожалуйста, напишите вопрос."

        try:
            response = self.client.chat(
                model="llama3.2:3b",
                prompt=text,
                temperature=0.7
            )

            if not response:
                return "Не удалось получить ответ от ИИ."

            return str(response).strip()

        except Exception as e:
            print("AI ERROR:", str(e), flush=True)
            return "Ошибка ИИ сервиса."
