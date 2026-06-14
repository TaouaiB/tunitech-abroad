from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from apps.cvs.models import CVUpload, CVParsedData
from apps.profiles.models import ProfileSkill
import uuid

class CVDeletionService:
    @classmethod
    def delete_cv(cls, user, cv_public_id: uuid.UUID):
        try:
            cv = CVUpload.objects.get(user=user, public_id=cv_public_id)
        except CVUpload.DoesNotExist:
            return {"success": False, "error": "CV not found"}

        with transaction.atomic():
            cv.soft_delete()
            
            if cv.file and hasattr(cv.file, 'path'):
                try:
                    import os
                    if os.path.exists(cv.file.path):
                        os.remove(cv.file.path)
                except Exception:
                    pass
            
            try:
                parsed_data = cv.parsed_data
                parsed_data.delete()
            except ObjectDoesNotExist:
                pass

            if hasattr(user, 'candidate_profile'):
                ProfileSkill.objects.filter(
                    profile=user.candidate_profile,
                    is_confirmed=False,
                    source='cv_upload'
                ).delete()

            try:
                from apps.analytics.services.events import UserEventService
                if UserEventService is not None:
                    UserEventService.record(user, "cv_deleted", {"cv_public_id": str(cv_public_id)})
            except (ImportError, AttributeError, Exception):
                pass
                
        return {"success": True}
