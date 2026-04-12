import os
from groq import Groq


class AIService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.client = Groq(api_key=self.api_key)

        # Быстрая и дешёвая модель для чата
        self.model = "llama-3.1-8b-instant"

        # Простой кэш, чтобы одинаковые вопросы не гонять в API повторно
        self.cache = {}

    def ask(self, user_question: str, context: str = "") -> str:
        user_question = (user_question or "").strip()

        if not user_question:
            return "Пожалуйста, напишите вопрос."

        if not self.api_key:
            return "Не настроен GROQ_API_KEY."

        cache_key = f"{user_question}|{context}".lower()
        if cache_key in self.cache:
            return self.cache[cache_key]

        system_prompt = (
            "Ты помощник по курсам и услугам школы. "
            "Отвечай только на русском языке. "
            "Отвечай кратко, понятно и по делу. "
            "Если в предоставленном контексте нет точного ответа, так и скажи."
        )

        user_content = user_question
        if context:
            user_content = (
                f"Контекст с сайта:\n{context}\n\n"
                f"Вопрос пользователя:\n{user_question}"
            )

        try:
            chat_completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.2,
                max_completion_tokens=500,
            )

            answer = (
                chat_completion.choices[0].message.content.strip()
                if chat_completion.choices
                and chat_completion.choices[0].message
                and chat_completion.choices[0].message.content
                else "Не удалось получить ответ от ИИ."
            )

            self.cache[cache_key] = answer
            return answer

        except Exception as e:
            print("GROQ ERROR:", str(e), flush=True)
            return "Ошибка при обращении к ИИ."
