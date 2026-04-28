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
