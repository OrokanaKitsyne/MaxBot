import unittest
from unittest.mock import MagicMock, patch

import max_api


class TestMaxApi(unittest.TestCase):
    @patch("max_api.requests.request")
    def test_request_max_sends_correct_request(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "ok"
        mock_request.return_value = mock_response

        result = max_api.request_max(
            method="POST",
            token="test-token",
            path="/messages",
            payload={"text": "Привет"},
            params={"chat_id": 123}
        )

        self.assertEqual(result, mock_response)

        mock_request.assert_called_once_with(
            method="POST",
            url="https://platform-api.max.ru/messages",
            headers={
                "Authorization": "test-token",
                "Content-Type": "application/json"
            },
            json={"text": "Привет"},
            params={"chat_id": 123},
            timeout=20
        )

    @patch("max_api.request_max")
    def test_send_message_without_attachments(self, mock_request_max):
        mock_response = MagicMock()
        mock_request_max.return_value = mock_response

        result = max_api.send_message(
            token="test-token",
            chat_id=123,
            text="Тестовое сообщение"
        )

        self.assertEqual(result, mock_response)

        mock_request_max.assert_called_once_with(
            "POST",
            "test-token",
            "/messages",
            payload={"text": "Тестовое сообщение"},
            params={"chat_id": 123}
        )

    @patch("max_api.request_max")
    def test_send_message_with_attachments(self, mock_request_max):
        attachments = [
            {
                "type": "inline_keyboard",
                "payload": {
                    "buttons": []
                }
            }
        ]

        mock_response = MagicMock()
        mock_request_max.return_value = mock_response

        result = max_api.send_message(
            token="test-token",
            chat_id=123,
            text="Сообщение с клавиатурой",
            attachments=attachments
        )

        self.assertEqual(result, mock_response)

        mock_request_max.assert_called_once_with(
            "POST",
            "test-token",
            "/messages",
            payload={
                "text": "Сообщение с клавиатурой",
                "attachments": attachments
            },
            params={"chat_id": 123}
        )

    def test_answer_callback_without_callback_id_returns_none(self):
        result = max_api.answer_callback(
            token="test-token",
            callback_id=None,
            text="Ответ"
        )

        self.assertIsNone(result)

    @patch("max_api.request_max")
    def test_answer_callback_without_attachments(self, mock_request_max):
        mock_response = MagicMock()
        mock_request_max.return_value = mock_response

        result = max_api.answer_callback(
            token="test-token",
            callback_id="callback-1",
            text="Ответ на callback"
        )

        self.assertEqual(result, mock_response)

        mock_request_max.assert_called_once_with(
            "POST",
            "test-token",
            "/answers",
            payload={
                "message": {
                    "text": "Ответ на callback"
                }
            },
            params={"callback_id": "callback-1"}
        )

    @patch("max_api.request_max")
    def test_answer_callback_with_attachments(self, mock_request_max):
        attachments = [
            {
                "type": "inline_keyboard",
                "payload": {
                    "buttons": []
                }
            }
        ]

        mock_response = MagicMock()
        mock_request_max.return_value = mock_response

        result = max_api.answer_callback(
            token="test-token",
            callback_id="callback-1",
            text="Ответ с клавиатурой",
            attachments=attachments
        )

        self.assertEqual(result, mock_response)

        mock_request_max.assert_called_once_with(
            "POST",
            "test-token",
            "/answers",
            payload={
                "message": {
                    "text": "Ответ с клавиатурой",
                    "attachments": attachments
                }
            },
            params={"callback_id": "callback-1"}
        )

    def test_delete_message_without_message_id_returns_none(self):
        result = max_api.delete_message(
            token="test-token",
            message_id=None
        )

        self.assertIsNone(result)

    @patch("max_api.request_max")
    def test_delete_message_with_message_id(self, mock_request_max):
        mock_response = MagicMock()
        mock_request_max.return_value = mock_response

        result = max_api.delete_message(
            token="test-token",
            message_id="message-123"
        )

        self.assertEqual(result, mock_response)

        mock_request_max.assert_called_once_with(
            "DELETE",
            "test-token",
            "/messages/message-123"
        )


if __name__ == "__main__":
    unittest.main()
