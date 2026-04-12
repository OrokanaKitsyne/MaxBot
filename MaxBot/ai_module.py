from ollamafreeapi import OllamaFreeAPI
from knowledge_base import WebsiteKnowledgeBase


class AIService:
    def __init__(self):
        self.client = OllamaFreeAPI()
        self.model = "deepseek-r1:latest"

        self.kb = WebsiteKnowledgeBase()
        self.kb.load()

    def ask(self, user_question: str) -> str:
        user_question = (user_question or "").strip()

        if not user_question:
            return "Пожалуйста, напишите вопрос."

        found_docs = self.kb.search(user_question, top_k=3)

        if found_docs:
            context_blocks = []
            sources = []

            for i, doc in enumerate(found_docs, start=1):
                context_blocks.append(f"[Фрагмент {i}]\n{doc['text']}")
                sources.append(doc["url"])

            context_text = "\n\n".join(context_blocks)
            sources_text = "\n".join(sorted(set(sources)))

            prompt = f"""
Ты — помощник по курсам и услугам.
Отвечай только на русском языке.
Отвечай только на основе контекста ниже.
Если в контексте нет точного ответа, честно скажи: "Я не нашёл точной информации на сайте".

Контекст:
{context_text}

Вопрос пользователя:
{user_question}

В конце кратко добавь:
Источники:
{sources_text}
"""
        else:
            prompt = f"""
Ты — помощник по курсам и услугам.
Отвечай только на русском языке.
Если информации нет, честно скажи:
"Я не нашёл точной информации на сайте".

Вопрос пользователя:
{user_question}
"""

        try:
            response = self.client.chat(
                model=self.model,
                prompt=prompt,
                temperature=0.2
            )

            if not response:
                return "Не удалось получить ответ от ИИ."

            return str(response).strip()

        except Exception as e:
            print("AI ERROR:", str(e), flush=True)
            return "Ошибка ИИ сервиса."
