import logging
from .client import OpenRouterClient
from .prompts import MATCH_EXPLANATION_PROMPT
from .usage import log_llm_request
import time

logger = logging.getLogger(__name__)

def explain_match(candidate_profile: str, job_description: str, score: int, missing_skills: str, user=None) -> str:
    """
    Provides an LLM-generated explanation of the deterministic match score.
    """
    prompt = MATCH_EXPLANATION_PROMPT.format(
        candidate_profile=candidate_profile,
        job_description=job_description,
        score=score,
        missing_skills=missing_skills
    )
    
    messages = [
        {"role": "system", "content": "You are a supportive career coach explaining a match score to a candidate. Be brief and encouraging."},
        {"role": "user", "content": prompt}
    ]
    
    client = OpenRouterClient()
    start_time = time.time()
    try:
        content, usage = client.chat(messages)
        latency_ms = int((time.time() - start_time) * 1000)
        log_llm_request(
            purpose="match_explanation",
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
            purpose="match_explanation",
            model_name=client.default_model,
            status="error",
            user=user,
            latency_ms=latency_ms,
            error_message=str(e)
        )
        return "Explanation is currently unavailable."
