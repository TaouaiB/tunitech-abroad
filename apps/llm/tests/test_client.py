import json
import urllib.error
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from apps.llm.services.client import OpenRouterClient

class OpenRouterClientTests(TestCase):

    @override_settings(LLM_ENABLED=False)
    def test_client_disabled_mode(self):
        client = OpenRouterClient()
        content, usage = client.chat([{"role": "user", "content": "Hello"}])
        self.assertIn("mocked", content)
        self.assertIn("total_tokens", usage)

    @override_settings(LLM_ENABLED=True, OPENROUTER_API_KEY="")
    def test_client_missing_api_key_raises_error(self):
        with self.assertRaises(ValueError):
            client = OpenRouterClient()
            client.chat([{"role": "user", "content": "Hello"}])

    @override_settings(LLM_ENABLED=True, OPENROUTER_API_KEY="test_key")
    @patch("urllib.request.urlopen")
    def test_client_success_response(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": "Hello world"}}],
            "usage": {"total_tokens": 10}
        }).encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        client = OpenRouterClient()
        content, usage = client.chat([{"role": "user", "content": "Hello"}])
        
        self.assertEqual(content, "Hello world")
        self.assertEqual(usage["total_tokens"], 10)

    @override_settings(LLM_ENABLED=True, OPENROUTER_API_KEY="test_key")
    @patch("urllib.request.urlopen")
    def test_client_http_error(self, mock_urlopen):
        # Setup mock to raise HTTPError
        fp = MagicMock()
        fp.read.return_value = b'{"error": "bad request"}'
        err = urllib.error.HTTPError(url="", code=400, msg="Bad Request", hdrs={}, fp=fp)
        mock_urlopen.side_effect = err

        client = OpenRouterClient()
        with self.assertRaises(urllib.error.HTTPError):
            client.chat([{"role": "user", "content": "Hello"}])
