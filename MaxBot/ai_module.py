import os
import requests


class AIService:
    def __init__(self):
        self.api_key = os.getenv("AI_API_KEY", "").strip()
        self.base_url = os.getenv("AI_BASE_URL", "").strip()
        self.model = os.getenv("AI_MODEL", "").strip()

    def is_configured(self) -> bool:
        return bool(self.api_key and self.base_url and self.model)

    def ask(self, user_text: str) -> str:
        user_text = (user_text or "").strip()

        if not user_text:
            return "Пожалуйста, напишите вопрос."

        if not self.is_configured():
            return (
                "ИИ-модуль пока не настроен. "
                "Добавьте AI_API_KEY, AI_BASE_URL и AI_MODEL в переменные окружения."
            )

        system_prompt = (
            "Ты — полезный учебный помощник по алгоритмам и программированию. "
            "Отвечай понятно, кратко и по делу. "
            "Если вопрос учебный, объясняй простыми словами и по шагам. "
            "Если уместно, приводи маленький пример."
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            "temperature": 0.4,
            "max_tokens": 500
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=60
            )

            print("AI STATUS:", response.status_code, flush=True)
            print("AI RESPONSE:", response.text[:1000], flush=True)

            response.raise_for_status()
            data = response.json()

            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )

            if not content:
                return "Не удалось получить ответ от ИИ."

            return content

        except requests.Timeout:
            return "Сервис ИИ не ответил вовремя. Попробуйте ещё раз."
        except requests.RequestException as e:
            print("AI ERROR:", str(e), flush=True)
            return "Ошибка при обращении к ИИ-сервису."
        except Exception as e:
            print("AI PARSE ERROR:", str(e), flush=True)
            return "Не удалось обработать ответ ИИ."
