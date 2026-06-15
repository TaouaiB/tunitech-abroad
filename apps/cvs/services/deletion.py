from django.db import transaction
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
            cls.delete_cv_record(cv)

            if hasattr(user, 'candidate_profile'):
                ProfileSkill.objects.filter(
                    profile=user.candidate_profile,
                    is_confirmed=False,
                    source='cv_upload'
                ).delete()

            try:
                from apps.analytics.services.user_event import UserEventService
                UserEventService.record_event(
                    event_type="cv_deleted",
                    user=user,
                    metadata={"cv_public_id": str(cv_public_id)},
                )
            except Exception:
                pass
                
            try:
                from apps.recommendations.services.staleness import RecommendationStalenessService
                RecommendationStalenessService.mark_user_recommendations_stale(user, reason="cv_deleted")
            except ImportError:
                pass

        return {"success": True}

    @staticmethod
    def delete_cv_record(cv: CVUpload) -> None:
        cv.soft_delete()

        if cv.file and hasattr(cv.file, 'path'):
            try:
                import os
                if os.path.exists(cv.file.path):
                    os.remove(cv.file.path)
            except Exception:
                pass

        CVParsedData.objects.filter(cv_upload=cv).delete()
