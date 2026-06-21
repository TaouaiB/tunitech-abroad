import time
import hashlib
from typing import Optional

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone

from .client import OpenRouterClient
from .usage import log_llm_request
from apps.llm.models import LLMRequestLog

User = get_user_model()

DAILY_LIMIT = 5

def run_llm_request(user_id, purpose, messages, model: Optional[str] = None):
    user = User.objects.filter(id=user_id).first() if user_id else None
    
    if user:
        today = timezone.now().date()
        daily_count = LLMRequestLog.objects.filter(
            user=user,
            created_at__date=today
        ).count()
        if daily_count >= DAILY_LIMIT:
            raise Exception("BLOCKED: Daily LLM request limit reached.")

    message_str = str(messages)
    cache_key = f"llm_cache_{hashlib.sha256(message_str.encode()).hexdigest()}"
    cached_response = cache.get(cache_key)
    if cached_response:
        return cached_response

    client = OpenRouterClient(default_model=model)

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
        cache.set(cache_key, content, timeout=86400 * 7)
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
