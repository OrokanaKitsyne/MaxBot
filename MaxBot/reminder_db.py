import os
from supabase import create_client


SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Не заданы SUPABASE_URL или SUPABASE_KEY")


supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


class ReminderDB:

    def get_parent(self, max_user_id):
        result = (
            supabase
            .table("parents")
            .select("*, groups(*)")
            .eq("max_user_id", int(max_user_id))
            .execute()
        )
        return result.data[0] if result.data else None

    def register_parent(self, max_user_id, parent_name, invite_code, chat_id=None):
        group_result = (
            supabase
            .table("groups")
            .select("*")
            .eq("invite_code", invite_code)
            .execute()
        )

        if not group_result.data:
            return None

        group = group_result.data[0]

        supabase.table("parents").upsert(
            {
                "max_user_id": int(max_user_id),
                "chat_id": int(chat_id) if chat_id else None,
                "parent_name": parent_name,
                "group_id": group["id"],
                "notifications_enabled": False
            },
            on_conflict="max_user_id"
        ).execute()

        return group

    def set_notifications(self, max_user_id, enabled):
        (
            supabase
            .table("parents")
            .update({"notifications_enabled": enabled})
            .eq("max_user_id", int(max_user_id))
            .execute()
        )

    def get_schedule(self, group_id):
        result = (
            supabase
            .table("lessons")
            .select("*")
            .eq("group_id", group_id)
            .order("lesson_date")
            .order("lesson_time")
            .execute()
        )
        return result.data or []

    def save_feedback(self, parent_id, lesson_id, rating):
        (
            supabase
            .table("feedback")
            .upsert(
                {
                    "parent_id": parent_id,
                    "lesson_id": lesson_id,
                    "rating": int(rating)
                },
                on_conflict="parent_id,lesson_id"
            )
            .execute()
        )

    def set_waiting_for_comment(self, max_user_id, lesson_id):
        (
            supabase
            .table("parents")
            .update({
                "waiting_for_comment": True,
                "pending_feedback_lesson_id": lesson_id
            })
            .eq("max_user_id", int(max_user_id))
            .execute()
        )

    def clear_waiting_for_comment(self, max_user_id):
        (
            supabase
            .table("parents")
            .update({
                "waiting_for_comment": False,
                "pending_feedback_lesson_id": None
            })
            .eq("max_user_id", int(max_user_id))
            .execute()
        )

    def save_feedback_comment(self, parent_id, lesson_id, comment):
        (
            supabase
            .table("feedback")
            .update({"comment": comment})
            .eq("parent_id", parent_id)
            .eq("lesson_id", lesson_id)
            .execute()
        )
