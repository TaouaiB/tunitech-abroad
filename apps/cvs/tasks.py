from celery import shared_task
from .services.parsing import CVParsingService

@shared_task
def parse_cv(cv_upload_id: int) -> None:
    CVParsingService.parse_by_id(cv_upload_id)
