import requests

BASE_URL = "https://platform-api.max.ru"


def request_max(method, token, path, payload=None, params=None):
    url = f"{BASE_URL}{path}"

    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }

    response = requests.request(
        method=method,
        url=url,
        headers=headers,
        json=payload,
        params=params,
        timeout=20
    )

    print(f"{method} {path} STATUS:", response.status_code, flush=True)
    print(f"{method} {path} RESPONSE:", response.text, flush=True)

    return response


def send_message(token, chat_id, text, attachments=None):
    payload = {"text": text}

    if attachments:
        payload["attachments"] = attachments

    return request_max(
        "POST",
        token,
        "/messages",
        payload=payload,
        params={"chat_id": chat_id}
    )


def answer_callback(token, callback_id, text, attachments=None):
    if not callback_id:
        return None

    message = {"text": text}

    if attachments:
        message["attachments"] = attachments

    payload = {
        "message": message
    }

    return request_max(
        "POST",
        token,
        "/answers",
        payload=payload,
        params={"callback_id": callback_id}
    )
