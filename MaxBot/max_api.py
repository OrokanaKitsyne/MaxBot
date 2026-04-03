import requests # type: ignore
import time

class MaxApiClient:
    def __init__(self, token):
        self.token = token
        self.base_url = "https://platform-api.max.ru"
        self.headers = {
        "Authorization": self.token,
        "Content-Type": "application/json"
        }

  

    def get_updates(self, marker=None):
        url = f"{self.base_url}/updates"

        params = {
            "timeout": 30,
            "limit": 100,
            "types": "message_created"
        }

        if marker is not None:
            params["marker"] = marker

        response = requests.get(
            url,
            headers=self.headers,
            params=params,
            timeout=35
        )

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            wait_seconds = int(retry_after) if retry_after and retry_after.isdigit() else 5
            print(f"Получен 429. Ждём {wait_seconds} сек.")
            time.sleep(wait_seconds)
            return [], marker

        response.raise_for_status()

        data = response.json()
        updates = data.get("updates", [])
        new_marker = data.get("marker", marker)

        return updates, new_marker

    def send_message(self, chat_id, text):
        url = f"{self.base_url}/messages"

        payload = {
            "chat_id": chat_id,
            "text": text
        }

        response = requests.post(url, headers=self.headers, json=payload, timeout=30)
        response.raise_for_status()

        return response.json()
