import json
from datetime import datetime
from pathlib import Path


class FeedbackBotLogic:
    """Логика второго бота для выдачи обратной связи по урокам."""

    def __init__(self, file_path="feedback_lessons.json"):
        self.file_path = Path(file_path)
        self.data = self.load_data()
        self.user_state = {}

    def load_data(self):
        with open(self.file_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def reload_data(self):
        self.data = self.load_data()

    def get_courses(self):
        return list(self.data.get("courses", {}).keys())

    def course_exists(self, course_name):
        return course_name in self.data.get("courses", {})

    def get_lessons(self, course_name):
        if not self.course_exists(course_name):
            return []

        lessons = self.data["courses"][course_name].get("lessons", {})
        return sorted(lessons.keys(), key=lambda value: int(value) if value.isdigit() else value)

    def lesson_exists(self, course_name, lesson_num):
        if not self.course_exists(course_name):
            return False

        lessons = self.data["courses"][course_name].get("lessons", {})
        return str(lesson_num) in lessons

    def set_course(self, user_id, course_name):
        self.user_state[str(user_id)] = {
            "course": course_name
        }

    def set_lesson(self, user_id, lesson_num):
        user_id = str(user_id)

        if user_id not in self.user_state:
            self.user_state[user_id] = {}

        self.user_state[user_id]["lesson"] = str(lesson_num)

    def get_state(self, user_id):
        return self.user_state.get(str(user_id), {})

    def reset_state(self, user_id):
        self.user_state.pop(str(user_id), None)

    def generate_feedback(self, user_id, lesson_type):
        today = datetime.now().strftime("%d.%m.%Y")

        state = self.get_state(user_id)
        course_name = state.get("course")
        lesson_num = state.get("lesson")

        if not course_name:
            return "Ошибка: сначала выберите курс."

        if not lesson_num:
            return "Ошибка: сначала выберите урок."

        if not self.lesson_exists(course_name, lesson_num):
            return "Ошибка: урок не найден в базе данных."

        lesson = self.data["courses"][course_name]["lessons"][str(lesson_num)]

        title = lesson.get("title", "Без темы")
        intro = lesson.get("intro", "")
        tasks = lesson.get("tasks", [])

        text = f"""Обратная связь урок №{lesson_num} от {today}

🌙 Добрый вечер, уважаемые родители!

🔥 Делюсь результатами работы на уроке «{title}» 🔥
"""

        if intro:
            text += f"\n{intro}\n"

        text += "\nНа уроке мы:\n"

        for task in tasks:
            task_text = str(task).strip()
            if task_text:
                text += f"✅ {task_text}\n"

        if lesson_type == "offline":
            text += f"""

Начислены астрокоины за урок №{lesson_num} от {today}
Количество астрокоинов, а также куда их потратить, можно посмотреть на сайте (Логин/пароль такие же как от платформы Алгоритмика)
http://algoritmika52.ru/
"""

        text += """
👍 На онлайн-платформе «Алгоритмика» предоставлен весь материал, пройденный на уроках и прогресс 📈 ребенка.

🔥 Удачной недели!"""

        return text.strip()
