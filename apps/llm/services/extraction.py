import json
import logging
from .client import OpenRouterClient
from .prompts import CV_EXTRACTION_PROMPT
from .safety import mask_sensitive_data
from .usage import log_llm_request
import time

logger = logging.getLogger(__name__)

def suggest_cv_extraction(cv_text, user=None):
    """
    Calls LLM to suggest structured data from CV text.
    """
    safe_text = mask_sensitive_data(cv_text)
    prompt = CV_EXTRACTION_PROMPT.format(cv_text=safe_text)
    
    messages = [
        {"role": "system", "content": "You are a helpful CV extraction assistant. Output only JSON."},
        {"role": "user", "content": prompt}
    ]
    
    client = OpenRouterClient()
    start_time = time.time()
    try:
        content, usage = client.chat(messages, response_format={"type": "json_object"})
        latency_ms = int((time.time() - start_time) * 1000)
        log_llm_request(
            purpose="cv_extraction",
            model_name=client.default_model,
            status="success",
            user=user,
            usage=usage,
            latency_ms=latency_ms
        )
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("LLM output was not valid JSON.")
            return {}
            
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        log_llm_request(
            purpose="cv_extraction",
            model_name=client.default_model,
            status="error",
            user=user,
            latency_ms=latency_ms,
            error_message=str(e)
        )
        return {}
