from ollamafreeapi import OllamaFreeAPI


class AIService:
    def __init__(self):
        self.client = OllamaFreeAPI()

    def ask(self, text: str) -> str:
        try:
            response = self.client.chat(
                model="llama3.2:3b",
                prompt=text,
                temperature=0.7
            )

            return response

        except Exception as e:
            print("AI ERROR:", str(e), flush=True)
            return "Ошибка ИИ сервиса"
