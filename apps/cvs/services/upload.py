import hashlib
import logging
from pathlib import Path
from typing import Any, cast

logger = logging.getLogger(__name__)

from django.conf import settings
from django.db import transaction
from apps.cvs.models import CVUpload
from apps.cvs.tasks import parse_cv

class CVUploadService:
    PDF_MIME_TYPES = {"application/pdf"}

    @classmethod
    def upload_cv(cls, user, uploaded_file, *, consent_accepted: bool) -> CVUpload:
        if not user or not getattr(user, "is_authenticated", False):
            raise ValueError("User must be authenticated")
        if not consent_accepted:
            raise ValueError("Consent must be accepted")

        cls._validate_pdf(uploaded_file)

        file_content = uploaded_file.read()
        file_hash = hashlib.sha256(file_content).hexdigest()
        uploaded_file.seek(0)
        
        with transaction.atomic():
            CVUpload.objects.filter(user=user).update(is_active=False)
            
            cv_upload = CVUpload(
                user=user,
                file=uploaded_file,
                original_filename=uploaded_file.name,
                file_hash=file_hash,
                file_size=uploaded_file.size,
                mime_type=uploaded_file.content_type or 'application/pdf',
                is_active=True,
                parse_status='pending'
            )
            cv_upload.save()
            
            try:
                from apps.privacy.services.consent import ConsentService
                ConsentService.record(
                    user=user,
                    consent_type="cv_processing",
                    consent_text="Consentement au traitement du CV pour analyse et matching.",
                    consent_version="1.0",
                    request_meta={"source_path": "dashboard_cv_upload"},
                )
            except Exception as e:
                logger.warning(f"Failed to record consent: {e}", exc_info=True)
                
            try:
                from apps.analytics.services.user_event import UserEventService
                UserEventService.record_event(
                    event_type="cv_uploaded",
                    user=user,
                    metadata={"cv_public_id": str(cv_upload.public_id)},
                )
            except Exception as e:
                logger.warning(f"Failed to record cv_uploaded event: {e}", exc_info=True)

            # Celery task proxy exposes delay() at runtime; cast keeps Pyright clean.
            transaction.on_commit(lambda: cast(Any, parse_cv).delay(cv_upload.id))
            
            def mark_stale():
                try:
                    from apps.recommendations.services.staleness import RecommendationStalenessService
                    RecommendationStalenessService.mark_user_recommendations_stale(user, reason="cv_uploaded")
                except ImportError:
                    pass
                except Exception as e:
                    logger.warning(f"Failed to mark recommendations stale: {e}", exc_info=True)
            transaction.on_commit(mark_stale)
        
        return cv_upload

    @classmethod
    def _validate_pdf(cls, uploaded_file) -> None:
        if uploaded_file is None:
            raise ValueError("CV file is required")

        max_size_bytes = settings.MAX_CV_UPLOAD_SIZE_MB * 1024 * 1024
        if uploaded_file.size > max_size_bytes:
            raise ValueError(f"File size must be under {settings.MAX_CV_UPLOAD_SIZE_MB}MB")

        filename = getattr(uploaded_file, "name", "")
        if Path(filename).suffix.lower() != ".pdf":
            raise ValueError("Only PDF files are allowed")

        content_type = getattr(uploaded_file, "content_type", "")
        if content_type not in cls.PDF_MIME_TYPES:
            raise ValueError("Only PDF files are allowed")
