import json
from datetime import datetime
from pathlib import Path


class FeedbackBotLogic:
    def __init__(self, file_path="feedback_lessons.json"):
        self.file_path = Path(file_path)
        self.data = self.load_data()
        self.user_state = {}

    def load_data(self):
        with open(self.file_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def get_courses(self):
        return list(self.data["courses"].keys())

    def get_lessons(self, course_name):
        return list(self.data["courses"][course_name]["lessons"].keys())

    def set_course(self, user_id, course_name):
        self.user_state[user_id] = {
            "course": course_name
        }

    def set_lesson(self, user_id, lesson_num):
        self.user_state[user_id]["lesson"] = lesson_num

    def generate_feedback(self, user_id, lesson_type):
        today = datetime.now().strftime("%d.%m.%Y")

        state = self.user_state.get(user_id)
        if not state:
            return "Ошибка: сначала выберите курс и урок."

        course_name = state["course"]
        lesson_num = state["lesson"]

        lesson = self.data["courses"][course_name]["lessons"][lesson_num]

        text = f"""Обратная связь урок №{lesson_num} от {today}

🌙 Добрый вечер, уважаемые родители!

🔥 Делюсь результатами работы на уроке «{lesson["title"]}» 🔥

{lesson["intro"]}

На уроке мы:
"""

        for task in lesson["tasks"]:
            text += f"✅ {task}\n"

        if lesson_type == "offline":
            text += f"""

Начислены астрокоины за урок №{lesson_num} от {today}
Количество астрокоинов, а также куда их потратить, можно посмотреть на сайте (Логин/пароль такие же как от платформы Алгоритмика)
http://algoritmika52.ru/
"""

        text += """
👍 На онлайн-платформе «Алгоритмика» предоставлен весь материал, пройденный на уроках и прогресс 📈 ребенка.

🔥 Удачной недели!"""

        return text
