from celery import shared_task
import logging
from apps.privacy.models import DeletionRequest
from apps.privacy.services.account_deletion import AccountDeletionService
from apps.privacy.services.maintenance import PrivacyMaintenanceService

logger = logging.getLogger(__name__)

@shared_task
def process_account_deletion(deletion_request_id):
    try:
        deletion_request = DeletionRequest.objects.get(id=deletion_request_id)
        # process_request returns a model instance, but celery tasks shouldn't return model instances if they are serialized.
        # So we just return the status.
        result = AccountDeletionService.process_request(deletion_request)
        return result.status
    except DeletionRequest.DoesNotExist:
        return "not_found"
    except Exception as e:
        logger.error(f"Error in process_account_deletion: {e}")
        return "error"

@shared_task
def cleanup_expired_quick_matches():
    try:
        return PrivacyMaintenanceService.cleanup_expired_quick_matches().message
    except Exception as e:
        logger.error(f"Error in cleanup_expired_quick_matches: {e}")
        return "error"

@shared_task
def delete_orphaned_cv_files():
    """
    Scans private CV media and reports files no longer referenced by active/all CV records.
    Currently implemented as dry-run to avoid accidental deletion of valuable user data.
    """
    try:
        return PrivacyMaintenanceService.report_orphaned_cv_files().message
    except Exception as e:
        logger.error(f"Error in delete_orphaned_cv_files: {e}")
        return "error"
