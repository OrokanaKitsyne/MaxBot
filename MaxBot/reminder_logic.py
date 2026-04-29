from reminder_db import ReminderDB


class ReminderBotLogic:
    def __init__(self):
        self.db = ReminderDB()

    def handle_update(self, data):
        event = self.extract_event(data)

        update_type = event["update_type"]
        chat_id = event["chat_id"]
        user_id = event["user_id"]
        user_name = event["user_name"]
        command = event["command"]
        callback_id = event["callback_id"]

        if not chat_id or not user_id:
            return None

        if update_type == "bot_started":
            return {
                "chat_id": chat_id,
                "text": self.get_start_text(command)
            }

        if update_type not in ("message_created", "message_callback"):
            return None

        if command == "reminder:schedule":
            return self.show_schedule(chat_id, user_id, callback_id)

        if command == "reminder:notifications_on":
            return self.enable_notifications(chat_id, user_id, callback_id)

        if command == "reminder:notifications_off":
            return self.disable_notifications(chat_id, user_id, callback_id)

        if command.startswith("feedback:rating:"):
            return self.save_feedback_rating(chat_id, user_id, command, callback_id)

        if command == "feedback:clear":
            return self.clear_feedback_message(chat_id, callback_id)

        return self.register_by_code(chat_id, user_id, user_name, command)

    def get_start_text(self, payload):
        if payload == "hello":
            return (
                "Здравствуйте! 😊\n\n"
                "Я бот-напоминалка о занятиях 📚\n\n"
                "Чтобы подключиться к расписанию, пришлите код группы, "
                "который выдал администратор.\n\n"
                "Пример: WEB2026"
            )

        return (
            "Здравствуйте! 😊\n\n"
            "Пришлите код группы, который выдал администратор."
        )

    def register_by_code(self, chat_id, user_id, user_name, code):
        group = self.db.register_parent(user_id, user_name, code, chat_id)

        if not group:
            return {
                "chat_id": chat_id,
                "text": "Код группы не найден 😔\n\nПроверьте код и отправьте его ещё раз."
            }

        return {
            "chat_id": chat_id,
            "text": (
                "✅ Связь с таблицей установлена!\n\n"
                f"👥 Вы привязаны к группе: {group['name']}\n"
                f"📚 Курс: {group['course_name']}\n\n"
                "Теперь вы можете выбрать действие:\n\n"
                "📅 «Посмотреть всё расписание» — покажет все занятия группы.\n"
                "🔔 «Включить уведомления» — бот будет напоминать о занятиях за сутки."
            ),
            "attachments": self.get_keyboard(False)
        }

    def show_schedule(self, chat_id, user_id, callback_id=None):
        parent = self.db.get_parent(user_id)

        if not parent:
            return {
                "chat_id": chat_id,
                "callback_id": callback_id,
                "text": "Сначала пришлите код группы 🔑"
            }

        lessons = self.db.get_schedule(parent["group_id"])
        group = parent["groups"]

        return {
            "chat_id": chat_id,
            "callback_id": callback_id,
            "text": (
                f"👥 Группа: {group['name']}\n"
                f"📚 Курс: {group['course_name']}\n\n"
                f"{self.format_schedule(lessons)}"
            ),
            "attachments": self.get_keyboard(
                parent.get("notifications_enabled", False)
            )
        }

    def enable_notifications(self, chat_id, user_id, callback_id=None):
        parent = self.db.get_parent(user_id)

        if not parent:
            return {
                "chat_id": chat_id,
                "callback_id": callback_id,
                "text": "Сначала пришлите код группы 🔑"
            }

        self.db.set_notifications(user_id, True)

        return {
            "chat_id": chat_id,
            "callback_id": callback_id,
            "text": (
                "🔔 Уведомления включены!\n\n"
                "Теперь бот будет напоминать о занятиях за сутки 📚\n\n"
                "📅 «Посмотреть всё расписание» — покажет все занятия группы.\n"
                "🔕 «Выключить уведомления» — отключит автоматические напоминания."
            ),
            "attachments": self.get_keyboard(True)
        }

    def disable_notifications(self, chat_id, user_id, callback_id=None):
        parent = self.db.get_parent(user_id)

        if not parent:
            return {
                "chat_id": chat_id,
                "callback_id": callback_id,
                "text": "Сначала пришлите код группы 🔑"
            }

        self.db.set_notifications(user_id, False)

        return {
            "chat_id": chat_id,
            "callback_id": callback_id,
            "text": (
                "🔕 Уведомления выключены.\n\n"
                "Автоматические напоминания больше не будут отправляться.\n\n"
                "📅 «Посмотреть всё расписание» — покажет все занятия группы.\n"
                "🔔 «Включить уведомления» — снова включит автоматические напоминания."
            ),
            "attachments": self.get_keyboard(False)
        }

    def save_feedback_rating(self, chat_id, user_id, command, callback_id=None):
        parts = command.split(":")

        if len(parts) != 4:
            return {
                "chat_id": chat_id,
                "callback_id": callback_id,
                "text": "Не удалось обработать оценку. Попробуйте ещё раз."
            }

        lesson_id = parts[2]
        rating = int(parts[3])

        parent = self.db.get_parent(user_id)

        if not parent:
            return {
                "chat_id": chat_id,
                "callback_id": callback_id,
                "text": "Сначала пришлите код группы 🔑"
            }

        self.db.save_feedback(parent["id"], lesson_id, rating)

        return {
            "chat_id": chat_id,
            "callback_id": callback_id,
            "text": (
                "Спасибо за обратную связь! 😊\n\n"
                f"Ваша оценка: {'⭐' * rating}\n\n"
                "Нажмите кнопку ниже, чтобы очистить сообщение 👇"
            ),
            "attachments": [
                {
                    "type": "inline_keyboard",
                    "payload": {
                        "buttons": [
                            [
                                {
                                    "type": "callback",
                                    "text": "🧹 Стереть сообщение",
                                    "payload": "feedback:clear"
                                }
                            ]
                        ]
                    }
                }
            ]
        }

    def clear_feedback_message(self, chat_id, callback_id=None):
        return {
            "chat_id": chat_id,
            "callback_id": callback_id,
            "text": "✅ Сообщение очищено",
            "attachments": []
        }

    def format_schedule(self, lessons):
        if not lessons:
            return "Расписание пока не добавлено 🕓"

        lines = ["📅 Расписание занятий:"]

        for lesson in lessons:
            lesson_time = str(lesson["lesson_time"])[:5]

            lines.append(
                f"📌 Урок №{lesson['lesson_number']} — "
                f"{lesson['lesson_date']} в {lesson_time}"
            )

        return "\n".join(lines)

    def get_keyboard(self, notifications_enabled):
        if notifications_enabled:
            notification_button = {
                "type": "callback",
                "text": "Выключить уведомления",
                "payload": "reminder:notifications_off"
            }
        else:
            notification_button = {
                "type": "callback",
                "text": "Включить уведомления",
                "payload": "reminder:notifications_on"
            }

        return [
            {
                "type": "inline_keyboard",
                "payload": {
                    "buttons": [
                        [
                            {
                                "type": "callback",
                                "text": "Посмотреть всё расписание",
                                "payload": "reminder:schedule"
                            }
                        ],
                        [notification_button]
                    ]
                }
            }
        ]

    def extract_event(self, data):
        update_type = data.get("update_type")

        chat_id = (
            data.get("chat_id")
            or data.get("message", {}).get("recipient", {}).get("chat_id")
            or data.get("message_callback", {}).get("chat_id")
            or data.get("callback", {}).get("chat_id")
        )

        if update_type == "message_callback":
            user = (
                data.get("callback", {}).get("user", {})
                or data.get("message_callback", {}).get("user", {})
                or {}
            )
        else:
            user = (
                data.get("user")
                or data.get("message", {}).get("sender", {})
                or data.get("callback", {}).get("user", {})
                or data.get("message_callback", {}).get("user", {})
                or {}
            )

        user_id = user.get("user_id")
        user_name = user.get("name") or user.get("first_name")

        text = (
            data.get("message", {}).get("body", {}).get("text")
            or data.get("message", {}).get("text")
        )

        payload = (
            data.get("payload")
            or data.get("callback", {}).get("payload")
            or data.get("message_callback", {}).get("payload")
        )

        callback_id = (
            data.get("callback", {}).get("callback_id")
            or data.get("message_callback", {}).get("callback_id")
            or data.get("callback_id")
        )

        return {
            "update_type": update_type,
            "chat_id": chat_id,
            "user_id": str(user_id) if user_id else None,
            "user_name": user_name,
            "command": str(payload or text or "").strip(),
            "callback_id": callback_id
        }
