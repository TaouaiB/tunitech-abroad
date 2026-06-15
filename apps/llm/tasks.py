from celery import shared_task

from .services.request_runner import run_llm_request


@shared_task
def run_llm_request_task(user_id, purpose, messages, model=None):
    """
    Background task wrapper for the LLM request service.
    """
    return run_llm_request(user_id, purpose, messages, model=model)
