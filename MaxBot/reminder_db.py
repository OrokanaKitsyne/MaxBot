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

    def register_parent(self, max_user_id, parent_name, invite_code):
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
                "parent_name": parent_name,
                "group_id": group["id"],
                "notifications_enabled": False
            },
            on_conflict="max_user_id"
        ).execute()

        return group

    def set_notifications(self, max_user_id, enabled):
        supabase.table("parents").update({
            "notifications_enabled": enabled
        }).eq("max_user_id", int(max_user_id)).execute()

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
