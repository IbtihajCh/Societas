import pytest
from unittest.mock import patch, MagicMock
import httpx

from models.client.amd_client import AMDClient
from models.config import AIConfig


class TestAMDClientInit:
    def test_init_with_default_config(self):
        client = AMDClient()
        assert client.config.amd_base_url == ""
        assert client.config.model_name == "gemma-2-9b-it"

    def test_init_with_custom_config(self):
        config = AIConfig(request_timeout=60.0)
        client = AMDClient(config)
        assert client.config.request_timeout == 60.0


class TestAMDClientChatCompletion:
    def test_successful_completion(self):
        config = AIConfig(max_retries=1)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Hello"}, "finish_reason": "stop"}],
            "usage": {"total_tokens": 5},
        }

        with patch.object(httpx.Client, "post", return_value=mock_resp) as mock_post:
            client = AMDClient(config)
            result = client.chat_completion(
                messages=[{"role": "user", "content": "Hi"}],
                temperature=0.5,
                max_tokens=100,
            )

        assert result["content"] == "Hello"
        assert result["finish_reason"] == "stop"
        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]
        assert call_args["json"]["temperature"] == 0.5
        assert call_args["json"]["max_tokens"] == 100

    def test_empty_choices_raises_error(self):
        config = AIConfig(max_retries=1)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"choices": []}

        with patch.object(httpx.Client, "post", return_value=mock_resp):
            client = AMDClient(config)
            with pytest.raises(ValueError, match="no choices in response"):
                client.chat_completion(messages=[{"role": "user", "content": "Hi"}])

    def test_retry_on_http_error(self):
        config = AIConfig(max_retries=2)
        mock_fail = MagicMock(spec=httpx.Response, status_code=500)
        mock_fail.raise_for_status.side_effect = httpx.HTTPStatusError("err", request=MagicMock(), response=mock_fail)
        mock_success = MagicMock()
        mock_success.json.return_value = {
            "choices": [{"message": {"content": "OK"}, "finish_reason": "stop"}]
        }

        with patch.object(httpx.Client, "post", side_effect=[mock_fail, mock_success]) as mock_post:
            client = AMDClient(config)
            result = client.chat_completion(messages=[{"role": "user", "content": "Hi"}])

        assert result["content"] == "OK"
        assert mock_post.call_count == 2

    def test_all_retries_exhausted(self):
        config = AIConfig(max_retries=2)
        mock_resp = MagicMock(spec=httpx.Response, status_code=500)
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError("err", request=MagicMock(), response=mock_resp)

        with patch.object(httpx.Client, "post", return_value=mock_resp):
            client = AMDClient(config)
            with pytest.raises(httpx.HTTPStatusError):
                client.chat_completion(messages=[{"role": "user", "content": "Hi"}])

    def test_timeout_retry(self):
        config = AIConfig(max_retries=2)
        with patch.object(httpx.Client, "post", side_effect=httpx.TimeoutException("timeout")):
            client = AMDClient(config)
            with pytest.raises(httpx.TimeoutException):
                client.chat_completion(messages=[{"role": "user", "content": "Hi"}])

    def test_close_client(self):
        client = AMDClient()
        with patch.object(httpx.Client, "close") as mock_close:
            client.close()
            mock_close.assert_called_once()
