import time
from typing import Optional

from django.contrib.auth import get_user_model

from .client import OpenRouterClient
from .usage import log_llm_request

User = get_user_model()


def run_llm_request(user_id, purpose, messages, model: Optional[str] = None):
    client = OpenRouterClient(default_model=model)
    user = User.objects.filter(id=user_id).first() if user_id else None

    start_time = time.time()
    try:
        content, usage = client.chat(messages)
        latency_ms = int((time.time() - start_time) * 1000)
        log_llm_request(
            purpose=purpose,
            model_name=model or client.default_model,
            status="success",
            user=user,
            usage=usage,
            latency_ms=latency_ms,
        )
        return content
    except Exception as exc:
        latency_ms = int((time.time() - start_time) * 1000)
        log_llm_request(
            purpose=purpose,
            model_name=model or client.default_model,
            status="error",
            user=user,
            latency_ms=latency_ms,
            error_message=str(exc),
        )
        raise
