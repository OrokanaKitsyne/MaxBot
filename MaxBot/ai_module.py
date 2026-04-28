import os
from groq import Groq
from knowledge_base import LocalKnowledgeBase
from knowledge import LocalKnowledge


class AIService:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            raise ValueError("Не задана переменная окружения GROQ_API_KEY")

        self.client = Groq(api_key=api_key)
        self.model = "llama-3.1-8b-instant"

        self.kb = LocalKnowledgeBase()  
        self.kl = LocalKnowledge()      

        self.cache = {}

    
    def get_fallback_text(self) -> str:
        return (
            "Я не нашёл точной информации по вашему вопросу.😔\n\n"
            "Свяжитесь с нами:\n"
            "☎️ Телефон: +7 (920) 069-02-00\n"
            "✉️ Email: nn@algoritmika.org"
        )

    
    def is_location_question(self, text: str) -> bool:
        text = text.lower()

        keywords = [
            "где", "адрес", "мест", "локац",
            "куда приходить", "где проходят",
            "где занятия", "площадк"
        ]

        return any(word in text for word in keywords)

   
    def ask(self, user_question: str) -> str:
        user_question = (user_question or "").strip()

        if not user_question:
            return "Пожалуйста, напишите вопрос."

        cache_key = user_question.lower()
        if cache_key in self.cache:
            return self.cache[cache_key]

        if self.is_location_question(user_question):
            return self.kl.get_locations_text()

        context = self.kb.get_context_for_query(
            user_question,
            top_k=3,
            max_chars=3500
        )

        if not context:
            return self.get_fallback_text()

        prompt = f"""
Ты консультант школы.
Отвечай только на русском языке.
Формат общения: дружелюбный, можно использовать смайлики.
Можно поддерживать нейтральную беседу. 
По возможности рекомендуй записаться на курс.
Используй только информацию из контекста.
Игнорируй технические данные.
Если нет ответа, скажи:
Я не нашёл точной информации по вашему вопросу.

Контекст:
{context}

Вопрос:
{user_question}
"""

        try:
            chat_completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты отвечаешь строго по базе знаний."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_completion_tokens=350,
            )

            answer = chat_completion.choices[0].message.content.strip()

            if not answer:
                return self.get_fallback_text()

            lowered = answer.lower()
            if "я не наш" in lowered:
                return self.get_fallback_text()

            self.cache[cache_key] = answer
            return answer

        except Exception as e:
            print("GROQ ERROR:", str(e))
            return self.get_fallback_text()
