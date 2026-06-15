import json
import logging
import urllib.request
import urllib.error
from django.conf import settings

logger = logging.getLogger(__name__)

class OpenRouterClient:
    """
    A simple client for OpenRouter API.
    """
    def __init__(self, api_key=None, base_url=None, default_model=None):
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.base_url = base_url or settings.OPENROUTER_BASE_URL
        self.default_model = default_model or settings.OPENROUTER_DEFAULT_MODEL
        self.enabled = settings.LLM_ENABLED

    def _make_request(self, messages, model=None, response_format=None, max_tokens=1024, temperature=0.7):
        if not self.enabled:
            logger.info("LLM is disabled. Returning mock response.")
            return self._get_mock_response(messages)

        if not self.api_key:
            logger.error("LLM_ENABLED is True but OPENROUTER_API_KEY is not set.")
            raise ValueError("OPENROUTER_API_KEY is not set.")

        url = self.base_url
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://tunitech-abroad.example.com",
            "X-Title": "TuniTech Abroad",
        }
        
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if response_format:
            payload["response_format"] = response_format

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result
        except urllib.error.HTTPError as e:
            logger.error("OpenRouter HTTP Error: %s", e.code)
            raise
        except urllib.error.URLError as e:
            logger.error("OpenRouter Network Error: %s", e.reason)
            raise
        except Exception as e:
            logger.error("OpenRouter Error: %s", str(e))
            raise

    def chat(self, messages, model=None, response_format=None, max_tokens=1024, temperature=0.7):
        """
        Sends a chat request and returns the parsed message content and usage info.
        """
        response = self._make_request(messages, model, response_format, max_tokens, temperature)
        
        if self.enabled:
            choices = response.get("choices", [])
            if not choices:
                return "", {}
            content = choices[0].get("message", {}).get("content", "")
            usage = response.get("usage", {})
            return content, usage
        else:
            return response.get("content", ""), response.get("usage", {})

    def _get_mock_response(self, messages):
        """
        Returns a generic mock response when disabled.
        """
        return {
            "content": '{"mocked": true}',
            "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20}
        }
