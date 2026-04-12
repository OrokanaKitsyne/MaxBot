import os
from groq import Groq
from knowledge_base import LocalKnowledgeBase


class AIService:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY", "").strip())
        self.model = "llama-3.1-8b-instant"
        self.kb = LocalKnowledgeBase()
        self.cache = {}

    def ask(self, user_question: str) -> str:
        user_question = (user_question or "").strip()

        if not user_question:
            return "Пожалуйста, напишите вопрос."

        cache_key = user_question.lower()
        if cache_key in self.cache:
            return self.cache[cache_key]

        docs = self.kb.search(user_question, top_k=3)
        context = "\n\n".join(doc["text"] for doc in docs[:3])

        prompt = f"""
Ты консультант школы Алгоритмика.
Отвечай только на русском языке.
Используй только контекст ниже.
Если точного ответа нет, скажи: "Я не нашёл точной информации."

Контекст:
{context}

Вопрос:
{user_question}
"""

        try:
            chat_completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты полезный консультант по курсам."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_completion_tokens=400,
            )

            answer = chat_completion.choices[0].message.content.strip()
            self.cache[cache_key] = answer
            return answer

        except Exception as e:
            print("GROQ ERROR:", str(e), flush=True)
            return "Ошибка при обращении к ИИ."
