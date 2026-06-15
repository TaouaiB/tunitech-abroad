import logging
from .client import OpenRouterClient
from .prompts import SKILL_SUGGESTION_PROMPT
from .usage import log_llm_request
import time

logger = logging.getLogger(__name__)

def suggest_skills(missing_skills: str, job_title: str, user=None) -> str:
    """
    Suggests concepts or topics to learn based on missing skills.
    """
    prompt = SKILL_SUGGESTION_PROMPT.format(
        missing_skills=missing_skills,
        job_title=job_title
    )
    
    messages = [
        {"role": "system", "content": "You are a technical career advisor. Provide short, practical learning suggestions."},
        {"role": "user", "content": prompt}
    ]
    
    client = OpenRouterClient()
    start_time = time.time()
    try:
        content, usage = client.chat(messages)
        latency_ms = int((time.time() - start_time) * 1000)
        log_llm_request(
            purpose="skill_suggestion",
            model_name=client.default_model,
            status="success",
            user=user,
            usage=usage,
            latency_ms=latency_ms
        )
        return content
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        log_llm_request(
            purpose="skill_suggestion",
            model_name=client.default_model,
            status="error",
            user=user,
            latency_ms=latency_ms,
            error_message=str(e)
        )
        return "Skill suggestions are currently unavailable."
