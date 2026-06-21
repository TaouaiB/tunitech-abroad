import json
import requests
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

    @override_settings(LLM_ENABLED=True)
    @patch("requests.post")
    def test_client_success_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello world"}}],
            "usage": {"total_tokens": 10}
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = OpenRouterClient(api_key="unit-test-key")
        content, usage = client.chat([{"role": "user", "content": "Hello"}])
        
        self.assertEqual(content, "Hello world")
        self.assertEqual(usage["total_tokens"], 10)

    @override_settings(LLM_ENABLED=True)
    @patch("requests.post")
    def test_client_http_error(self, mock_post):
        # Setup mock to raise HTTPError
        err_response = MagicMock()
        err_response.status_code = 400
        err = requests.exceptions.HTTPError("Bad Request", response=err_response)
        mock_post.side_effect = err

        client = OpenRouterClient(api_key="unit-test-key")
        with self.assertRaises(requests.exceptions.HTTPError):
            client.chat([{"role": "user", "content": "Hello"}])
