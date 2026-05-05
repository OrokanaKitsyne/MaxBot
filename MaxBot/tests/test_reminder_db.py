import importlib
import os
import unittest
from unittest.mock import MagicMock, patch


class TestReminderDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["SUPABASE_URL"] = "https://example.supabase.co"
        os.environ["SUPABASE_KEY"] = "fake-key"

    def setUp(self):
        import reminder_db

        self.reminder_db = reminder_db
        self.db = reminder_db.ReminderDB()

        self.mock_supabase = MagicMock()
        self.reminder_db.supabase = self.mock_supabase

    def make_chain(self, data=None):
        chain = MagicMock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.order.return_value = chain
        chain.update.return_value = chain
        chain.upsert.return_value = chain

        result = MagicMock()
        result.data = data if data is not None else []
        chain.execute.return_value = result

        return chain

    def test_get_parent_returns_parent_when_found(self):
        parent = {
            "id": 1,
            "max_user_id": 123,
            "parent_name": "Иван",
            "groups": {
                "course_name": "Python"
            }
        }

        chain = self.make_chain(data=[parent])
        self.mock_supabase.table.return_value = chain

        result = self.db.get_parent("123")

        self.assertEqual(result, parent)
        self.mock_supabase.table.assert_called_once_with("parents")
        chain.eq.assert_called_once_with("max_user_id", 123)

    def test_get_parent_returns_none_when_not_found(self):
        chain = self.make_chain(data=[])
        self.mock_supabase.table.return_value = chain

        result = self.db.get_parent("123")

        self.assertIsNone(result)

    def test_register_parent_returns_none_when_invite_code_not_found(self):
        chain = self.make_chain(data=[])
        self.mock_supabase.table.return_value = chain

        result = self.db.register_parent(
            max_user_id="123",
            parent_name="Иван",
            invite_code="BAD-CODE",
            chat_id="555"
        )

        self.assertIsNone(result)

    def test_register_parent_upserts_and_returns_group(self):
        group = {
            "id": 10,
            "course_name": "Python",
            "invite_code": "ABC123"
        }

        group_chain = self.make_chain(data=[group])
        parents_chain = self.make_chain(data=[])

        self.mock_supabase.table.side_effect = [
            group_chain,
            parents_chain
        ]

        result = self.db.register_parent(
            max_user_id="123",
            parent_name="Иван",
            invite_code="ABC123",
            chat_id="555"
        )

        self.assertEqual(result, group)

        parents_chain.upsert.assert_called_once_with(
            {
                "max_user_id": 123,
                "chat_id": 555,
                "parent_name": "Иван",
                "group_id": 10,
                "notifications_enabled": False
            },
            on_conflict="max_user_id"
        )

    def test_set_notifications_updates_parent(self):
        chain = self.make_chain()
        self.mock_supabase.table.return_value = chain

        self.db.set_notifications("123", True)

        self.mock_supabase.table.assert_called_once_with("parents")
        chain.update.assert_called_once_with({"notifications_enabled": True})
        chain.eq.assert_called_once_with("max_user_id", 123)
        chain.execute.assert_called_once()

    def test_get_schedule_returns_lessons(self):
        lessons = [
            {
                "id": 1,
                "lesson_date": "2026-05-05",
                "lesson_time": "12:00"
            },
            {
                "id": 2,
                "lesson_date": "2026-05-06",
                "lesson_time": "13:00"
            }
        ]

        chain = self.make_chain(data=lessons)
        self.mock_supabase.table.return_value = chain

        result = self.db.get_schedule(group_id=10)

        self.assertEqual(result, lessons)
        self.mock_supabase.table.assert_called_once_with("lessons")
        chain.eq.assert_called_once_with("group_id", 10)
        self.assertEqual(chain.order.call_count, 2)

    def test_get_schedule_returns_empty_list_when_no_data(self):
        chain = self.make_chain(data=None)
        self.mock_supabase.table.return_value = chain

        result = self.db.get_schedule(group_id=10)

        self.assertEqual(result, [])

    def test_save_feedback_upserts_rating(self):
        chain = self.make_chain()
        self.mock_supabase.table.return_value = chain

        self.db.save_feedback(
            parent_id=1,
            lesson_id=2,
            rating="5"
        )

        self.mock_supabase.table.assert_called_once_with("feedback")
        chain.upsert.assert_called_once_with(
            {
                "parent_id": 1,
                "lesson_id": 2,
                "rating": 5
            },
            on_conflict="parent_id,lesson_id"
        )
        chain.execute.assert_called_once()

    def test_set_waiting_for_comment_updates_parent(self):
        chain = self.make_chain()
        self.mock_supabase.table.return_value = chain

        self.db.set_waiting_for_comment(
            max_user_id="123",
            lesson_id=7
        )

        chain.update.assert_called_once_with(
            {
                "waiting_for_comment": True,
                "pending_feedback_lesson_id": 7
            }
        )
        chain.eq.assert_called_once_with("max_user_id", 123)
        chain.execute.assert_called_once()

    def test_clear_waiting_for_comment_updates_parent(self):
        chain = self.make_chain()
        self.mock_supabase.table.return_value = chain

        self.db.clear_waiting_for_comment(max_user_id="123")

        chain.update.assert_called_once_with(
            {
                "waiting_for_comment": False,
                "pending_feedback_lesson_id": None
            }
        )
        chain.eq.assert_called_once_with("max_user_id", 123)
        chain.execute.assert_called_once()

    def test_save_feedback_comment_updates_feedback(self):
        chain = self.make_chain()
        self.mock_supabase.table.return_value = chain

        self.db.save_feedback_comment(
            parent_id=1,
            lesson_id=2,
            comment="Хороший урок"
        )

        self.mock_supabase.table.assert_called_once_with("feedback")
        chain.update.assert_called_once_with({"comment": "Хороший урок"})

        calls = chain.eq.call_args_list
        self.assertEqual(calls[0].args, ("parent_id", 1))
        self.assertEqual(calls[1].args, ("lesson_id", 2))

        chain.execute.assert_called_once()


if __name__ == "__main__":
    unittest.main()
