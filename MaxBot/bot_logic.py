import os
import re
import requests
from datetime import datetime
from ai_module import AIService


class BotLogic:
    def __init__(self):
        self.ai = AIService()
        self.user_states = {}
        self.google_script_url = os.getenv("GOOGLE_SCRIPT_URL", "").strip()

    def get_start_text(self) -> str:
        return (
            "👋 Привет! Я бот-консультант Алгоритмики.\n\n"
            "Я могу рассказать об обучении, курсах и ответить на ваши вопросы 😊\n"
            "Выберите кнопку ниже или просто напишите сообщение."
        )

    def get_courses_text(self) -> str:
        return (
            "📚 Вот список курсов:\n\n"
            "💻 Факультет программирования:\n"
            "• 7–9 лет — Компьютерная грамотность\n"
            "• 9–10 лет — Визуальное программирование\n"
            "• 9–14 лет — Видеоблогинг\n"
            "• 9–14 лет — Графический дизайн\n"
            "• 10–11 лет — Геймдизайн\n"
            "• 11–13 лет — Создание веб-сайтов\n"
            "• 12–16 лет — Разработка игр на Юнити\n"
            "• 14–17 лет — Питон Про\n"
            "• 15–18 лет — Веб-разработка\n\n"
            "🧮 Факультет математики:\n"
            "• 6–8 лет — Математика+\n"
            "• 9–13 лет — Математика+\n\n"
            "✍️ Если хотите записаться, напишите: Записаться"
        )

    def get_contacts_text(self) -> str:
        return (
            "📞 Контакты Алгоритмики:\n\n"
            "Телефон: +7 (920) 069-02-00\n"
            "Email: nn@algoritmika.org\n"
            "🌐 Официальный сайт: https://algoritmika.org/ru"
        )

    def get_help_text(self) -> str:
        return (
            "🧭 Я помогу подобрать подходящий курс для ребёнка 👩‍💻\n\n"
            "Вы можете:\n"
            "• 📚 посмотреть список курсов\n"
            "• 📍 узнать места обучения\n"
            "• ❓ задать вопрос о курсах\n"
            "• ✍️ оставить заявку на запись\n"
            "• 📞 получить контакты\n\n"
            "Для записи напишите: Записаться 😊"
        )

    def normalize_phone(self, phone: str) -> str | None:
    """
    Принимает варианты:
    +7 999 123-45-67
    8 999 123 45 67
    89326065656
    79326065656
    9326065656
    +79326065656

    Возвращает телефон в формате +7XXXXXXXXXX
    или None, если номер некорректный.
    """

    if not phone:
        return None

    digits = re.sub(r"\D", "", phone)

   
    if len(digits) == 10:
        digits = "7" + digits


    elif len(digits) == 11:
        if digits.startswith("8"):
            digits = "7" + digits[1:]
        elif digits.startswith("7"):
            digits = digits
        else:
            return None
    else:
        return None

    return "+" + digits

    def is_valid_email(self, email: str) -> bool:
        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        return bool(re.match(pattern, email))

    def send_application_to_google_sheets(self, application: dict) -> bool:
        if not self.google_script_url:
            print("GOOGLE_SCRIPT_URL не задан", flush=True)
            return False

        prepared_application = {
            "date": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            "name": str(application.get("name", "")),
            "phone": str(application.get("phone", "")),
            "email": str(application.get("email", "")),
            "user_id": str(application.get("user_id", "")),
            "chat_id": str(application.get("chat_id", ""))
        }

        try:
            response = requests.post(
                self.google_script_url,
                json=prepared_application,
                timeout=10
            )

            print("GOOGLE SHEETS STATUS:", response.status_code, flush=True)
            print("GOOGLE SHEETS RESPONSE:", response.text, flush=True)

            return response.status_code == 200

        except Exception as e:
            print("Ошибка отправки заявки в Google Sheets:", e, flush=True)
            return False

    def start_application(self, user_id: str) -> str:
        self.user_states[user_id] = {
            "step": "name",
            "data": {}
        }

        return (
            "Отлично, помогу оставить заявку 😊\n\n"
            "Как вас зовут? ✍️"
        )

    def process_application_step(self, user_id: str, text: str) -> str:
        state = self.user_states.get(user_id)

        if not state:
            return ""

        step = state["step"]
        data = state["data"]

        if step == "name":
            if len(text.strip()) < 2:
                return "Пожалуйста, напишите ваше имя 😊"

            data["name"] = text.strip()
            state["step"] = "phone"

            return (
                "Спасибо! 😊 Теперь оставьте номер телефона.\n\n"
            )

        if step == "phone":
            normalized_phone = self.normalize_phone(text)

            if not normalized_phone:
                state["step"] = "phone"

                return (
                    "Похоже, номер телефона введён некорректно 😕\n\n"
                    "Пожалуйста, отправьте номер ещё раз.\n\n"
                    "Подойдут такие форматы:\n"
                    "📞 +7 999 123-45-67\n"
                    "📞 8 999 123 45 67\n"
                    "📞 79991234567\n"
                    "📞 9991234567"
                )

            data["phone"] = normalized_phone
            state["step"] = "email"

            return (
                "Отлично! ✅ Номер сохранён.\n\n"
                "Теперь укажите электронную почту.\n"
                "Например: example@mail.ru ✉️"
            )

        if step == "email":
            if not self.is_valid_email(text):
                state["step"] = "email"

                return (
                    "Похоже, email введён некорректно 😕\n\n"
                    "Пожалуйста, укажите почту в формате:\n"
                    "example@mail.ru"
                )

            data["email"] = text.strip()
            data["user_id"] = user_id
            data["chat_id"] = user_id

            success = self.send_application_to_google_sheets(data)

            self.user_states.pop(user_id, None)

            if success:
                return (
                    "Спасибо! Заявка отправлена 😊\n"
                    "Менеджер свяжется с вами в ближайшее время 📞"
                )

            return (
                "Заявку не удалось отправить автоматически 😕\n\n"
                "Пожалуйста, свяжитесь с нами напрямую:\n"
                "📞 Телефон: +7 (920) 069-02-00\n"
                "✉️ Email: nn@algoritmika.org"
            )

        return self.get_help_text()

    def get_response(self, text: str, user_id: str = "default") -> str:
        text = (text or "").strip()
        lowered = text.lower()

        if not text:
            return "Пожалуйста, напишите сообщение 😊"

        if user_id in self.user_states:
            return self.process_application_step(user_id, text)

        if lowered == "/start":
            return self.get_start_text()

        if lowered == "список курсов":
            return self.get_courses_text()

        if lowered == "контакты":
            return self.get_contacts_text()

        if lowered == "помощь":
            return self.get_help_text()

        if lowered in ["записаться", "запись", "оставить заявку", "хочу записаться"]:
            return self.start_application(user_id)

        return self.ai.ask(text)
