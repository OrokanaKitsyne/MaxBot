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
            "Я не нашёл точной информации по вашему вопросу 😕\n\n"
            "Но вы можете оставить заявку, и менеджер всё уточнит для вас 😊\n\n"
            "📞 Телефон: +7 (920) 069-02-00\n"
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
            return "Пожалуйста, напишите свой вопрос 😊"

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
            context = "Контекст по вопросу не найден."

        prompt = f"""
Ты — дружелюбный консультант школы программирования и математики Алгоритмика.

Главная задача:
Помогать пользователю, отвечать дружелюбно и поддерживать естественную беседу.

Правила ответа:
1. Отвечай только на русском языке.
2. Общайся тепло, понятно и дружелюбно.
3. В каждом ответе используй 1–2 уместных смайлика.
4. Если пользователь просто общается, здоровается, спрашивает "как дела", благодарит или пишет что-то нейтральное — отвечай естественно. Для обычной беседы не требуй информации из контекста.
5. Если вопрос связан с курсами, обучением, возрастом ребёнка, записью, контактами, расписанием, адресами или школой — используй только информацию из контекста.
6. Если вопрос связан со школой или курсами, но в контексте нет точной информации, ответь:
"Я не нашёл точной информации по вашему вопросу 😕
Но вы можете оставить заявку, и менеджер всё уточнит для вас 😊"
7. Не придумывай цены, расписание, адреса, акции, преподавателей и условия, если их нет в контексте.
8. По возможности мягко предлагай записаться на курс или оставить заявку, но не будь навязчивым.
9. Отвечай кратко: 2–5 предложений.

Контекст:
{context}

Сообщение пользователя:
{user_question}
"""

        try:
            chat_completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Ты дружелюбный русскоязычный консультант Алгоритмики. "
                            "Ты можешь поддерживать обычную беседу. "
                            "Факты о школе, курсах, ценах, адресах и расписании бери только из контекста."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_completion_tokens=350,
            )

            answer = chat_completion.choices[0].message.content.strip()

            if not answer:
                return self.get_fallback_text()

            self.cache[cache_key] = answer
            return answer

        except Exception as e:
            print("GROQ ERROR:", str(e), flush=True)
            return self.get_fallback_text()
