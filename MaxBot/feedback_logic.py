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
        return list(self.data.get("courses", {}).keys())

    def course_exists(self, course_name):
        return course_name in self.data.get("courses", {})

    def get_lessons(self, course_name):
        if not self.course_exists(course_name):
            return []

        lessons = self.data["courses"][course_name].get("lessons", {})

        return sorted(
            lessons.keys(),
            key=lambda value: int(value) if str(value).isdigit() else str(value)
        )

    def lesson_exists(self, course_name, lesson_num):
        if not self.course_exists(course_name):
            return False

        return str(lesson_num) in self.data["courses"][course_name].get("lessons", {})

    def get_state(self, user_id):
        return self.user_state.get(str(user_id), {})

    def set_course(self, user_id, course_name):
        self.user_state[str(user_id)] = {
            "course": course_name
        }

    def set_lesson(self, user_id, lesson_num):
        user_id = str(user_id)

        if user_id not in self.user_state:
            self.user_state[user_id] = {}

        self.user_state[user_id]["lesson"] = str(lesson_num)

    def generate_feedback(self, user_id, lesson_type):
        today = datetime.now().strftime("%d.%m.%Y")

        state = self.get_state(user_id)

        if not state:
            return "Ошибка: сначала выберите курс и урок."

        course_name = state.get("course")
        lesson_num = state.get("lesson")

        if not course_name:
            return "Ошибка: сначала выберите курс."

        if not lesson_num:
            return "Ошибка: сначала выберите урок."

        if not self.lesson_exists(course_name, lesson_num):
            return "Ошибка: выбранный урок не найден."

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
