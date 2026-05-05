import json
import os
import tempfile
import unittest

from feedback_logic import FeedbackBotLogic


class TestFeedbackBotLogic(unittest.TestCase):
    def create_temp_json(self, data):
        temp = tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            encoding="utf-8",
            suffix=".json"
        )
        json.dump(data, temp, ensure_ascii=False, indent=2)
        temp.close()
        return temp.name

    def create_feedback_data(self):
        return {
            "courses": {
                "Геймдизайн": {
                    "lessons": {
                        "1": {
                            "title": "Введение в геймдизайн",
                            "intro": "Сегодня познакомились с основами создания игр.",
                            "tasks": [
                                "Разобрали понятие игрового жанра",
                                "Создали первую идею игры"
                            ]
                        },
                        "2": {
                            "title": "Игровые механики",
                            "intro": "Изучили основные игровые механики.",
                            "tasks": [
                                "Определили правила игры",
                                "Продумали действия игрока"
                            ]
                        },
                        "10": {
                            "title": "Финальный проект",
                            "intro": "Начали работу над финальным проектом.",
                            "tasks": [
                                "Составили план проекта"
                            ]
                        }
                    }
                },
                "Python": {
                    "lessons": {
                        "1": {
                            "title": "Переменные",
                            "intro": "Изучили переменные в Python.",
                            "tasks": [
                                "Создали первую программу",
                                "Разобрали типы данных"
                            ]
                        }
                    }
                }
            }
        }

    def create_logic(self):
        path = self.create_temp_json(self.create_feedback_data())
        logic = FeedbackBotLogic(file_path=path)
        return logic, path

    def test_load_data(self):
        logic, path = self.create_logic()
        try:
            self.assertIn("courses", logic.data)
            self.assertIn("Геймдизайн", logic.data["courses"])
        finally:
            os.remove(path)

    def test_get_courses(self):
        logic, path = self.create_logic()
        try:
            courses = logic.get_courses()

            self.assertIn("Геймдизайн", courses)
            self.assertIn("Python", courses)
            self.assertEqual(len(courses), 2)
        finally:
            os.remove(path)

    def test_course_exists(self):
        logic, path = self.create_logic()
        try:
            self.assertTrue(logic.course_exists("Геймдизайн"))
            self.assertTrue(logic.course_exists("Python"))
            self.assertFalse(logic.course_exists("Несуществующий курс"))
        finally:
            os.remove(path)

    def test_get_lessons_returns_sorted_lessons(self):
        logic, path = self.create_logic()
        try:
            lessons = logic.get_lessons("Геймдизайн")

            self.assertEqual(lessons, ["1", "2", "10"])
        finally:
            os.remove(path)

    def test_get_lessons_for_unknown_course_returns_empty_list(self):
        logic, path = self.create_logic()
        try:
            lessons = logic.get_lessons("Несуществующий курс")

            self.assertEqual(lessons, [])
        finally:
            os.remove(path)

    def test_lesson_exists(self):
        logic, path = self.create_logic()
        try:
            self.assertTrue(logic.lesson_exists("Геймдизайн", "1"))
            self.assertTrue(logic.lesson_exists("Геймдизайн", 2))
            self.assertFalse(logic.lesson_exists("Геймдизайн", "999"))
            self.assertFalse(logic.lesson_exists("Несуществующий курс", "1"))
        finally:
            os.remove(path)

    def test_get_state_empty_by_default(self):
        logic, path = self.create_logic()
        try:
            state = logic.get_state("user-1")

            self.assertEqual(state, {})
        finally:
            os.remove(path)

    def test_set_course_saves_user_state(self):
        logic, path = self.create_logic()
        try:
            logic.set_course("user-1", "Геймдизайн")

            state = logic.get_state("user-1")
            self.assertEqual(state["course"], "Геймдизайн")
        finally:
            os.remove(path)

    def test_set_lesson_saves_user_state(self):
        logic, path = self.create_logic()
        try:
            logic.set_course("user-1", "Геймдизайн")
            logic.set_lesson("user-1", 2)

            state = logic.get_state("user-1")
            self.assertEqual(state["lesson"], "2")
        finally:
            os.remove(path)

    def test_set_lesson_without_course_creates_state(self):
        logic, path = self.create_logic()
        try:
            logic.set_lesson("user-1", 1)

            state = logic.get_state("user-1")
            self.assertEqual(state["lesson"], "1")
            self.assertNotIn("course", state)
        finally:
            os.remove(path)

    def test_generate_feedback_without_state_returns_error(self):
        logic, path = self.create_logic()
        try:
            result = logic.generate_feedback("user-1", "online")

            self.assertEqual(result, "Ошибка: сначала выберите курс и урок.")
        finally:
            os.remove(path)

    def test_generate_feedback_without_lesson_returns_error(self):
        logic, path = self.create_logic()
        try:
            logic.set_course("user-1", "Геймдизайн")

            result = logic.generate_feedback("user-1", "online")

            self.assertEqual(result, "Ошибка: сначала выберите урок.")
        finally:
            os.remove(path)

    def test_generate_feedback_with_unknown_lesson_returns_error(self):
        logic, path = self.create_logic()
        try:
            logic.set_course("user-1", "Геймдизайн")
            logic.set_lesson("user-1", "999")

            result = logic.generate_feedback("user-1", "online")

            self.assertEqual(result, "Ошибка: выбранный урок не найден.")
        finally:
            os.remove(path)

    def test_generate_online_feedback_contains_lesson_data(self):
        logic, path = self.create_logic()
        try:
            logic.set_course("user-1", "Геймдизайн")
            logic.set_lesson("user-1", "1")

            result = logic.generate_feedback("user-1", "online")

            self.assertIn("Обратная связь урок №1", result)
            self.assertIn("Введение в геймдизайн", result)
            self.assertIn("Сегодня познакомились с основами создания игр.", result)
            self.assertIn("Разобрали понятие игрового жанра", result)
            self.assertIn("Создали первую идею игры", result)
            self.assertNotIn("Начислены астрокоины", result)
        finally:
            os.remove(path)

    def test_generate_offline_feedback_contains_astrocoins(self):
        logic, path = self.create_logic()
        try:
            logic.set_course("user-1", "Геймдизайн")
            logic.set_lesson("user-1", "1")

            result = logic.generate_feedback("user-1", "offline")

            self.assertIn("Обратная связь урок №1", result)
            self.assertIn("Начислены астрокоины", result)
            self.assertIn("http://algoritmika52.ru/", result)
        finally:
            os.remove(path)

    def test_generate_feedback_course_missing_in_state(self):
        logic, path = self.create_logic()
        try:
            logic.set_lesson("user-1", "1")

            result = logic.generate_feedback("user-1", "online")

            self.assertEqual(result, "Ошибка: сначала выберите курс.")
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
