import time
from typing import Optional
from django.contrib.auth import get_user_model
from apps.llm.models import LLMRequestLog

User = get_user_model()

def log_llm_request(
    purpose: str,
    model_name: str,
    status: str,
    user: Optional[User] = None,
    provider: str = "openrouter",
    usage: Optional[dict] = None,
    latency_ms: Optional[int] = None,
    error_message: Optional[str] = None
) -> LLMRequestLog:
    """
    Logs an LLM request to the database.
    """
    prompt_tokens = usage.get("prompt_tokens") if usage else None
    completion_tokens = usage.get("completion_tokens") if usage else None
    total_tokens = usage.get("total_tokens") if usage else None

    return LLMRequestLog.objects.create(
        user=user,
        purpose=purpose,
        provider=provider,
        model_name=model_name,
        status=status,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        latency_ms=latency_ms,
        error_message=error_message
    )
