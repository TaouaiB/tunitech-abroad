import logging
from celery import shared_task
from .services.parsing import CVParsingService
from .models import CVUpload

logger = logging.getLogger(__name__)

@shared_task
def parse_cv(cv_upload_id: int) -> None:
    try:
        CVParsingService.parse_by_id(cv_upload_id)
    except Exception as e:
        logger.exception(f"Error parsing CV {cv_upload_id}: {e}")
        try:
            cv = CVUpload.all_objects.get(id=cv_upload_id)
            if cv.parse_status in ['pending', 'processing']:
                cv.parse_status = 'failed'
                cv.parse_error = "An unexpected error occurred during parsing. Please try again or upload another CV."
                cv.save(update_fields=['parse_status', 'parse_error'])
        except Exception:
            pass
