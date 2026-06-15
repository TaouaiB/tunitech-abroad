import os
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.cvs.models import CVUpload
from apps.matching.models import QuickMatchSession


@dataclass(frozen=True)
class MaintenanceResult:
    success: bool
    message: str
    count: int = 0


class PrivacyMaintenanceService:
    @staticmethod
    def cleanup_expired_quick_matches() -> MaintenanceResult:
        cutoff = timezone.now() - timedelta(hours=24)
        deleted_count, _ = QuickMatchSession.objects.filter(
            created_at__lt=cutoff,
        ).delete()
        return MaintenanceResult(
            success=True,
            message=f"Deleted {deleted_count} expired sessions",
            count=deleted_count,
        )

    @staticmethod
    def report_orphaned_cv_files() -> MaintenanceResult:
        media_root = settings.PRIVATE_MEDIA_ROOT
        cvs_dir = os.path.join(media_root, "cvs")

        if not os.path.exists(cvs_dir):
            return MaintenanceResult(success=True, message="No cvs directory found")

        referenced_paths = {
            cv.file.name
            for cv in CVUpload.all_objects.exclude(file="").iterator()
            if cv.file and cv.file.name
        }

        orphaned_count = 0
        for root, _dirs, files in os.walk(cvs_dir):
            for filename in files:
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, media_root)
                if rel_path not in referenced_paths:
                    orphaned_count += 1

        return MaintenanceResult(
            success=True,
            message=f"Dry run found {orphaned_count} orphaned files",
            count=orphaned_count,
        )
