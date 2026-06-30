from dataclasses import dataclass
import mimetypes

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404

from apps.core.models import AdminFileAccessLog
from apps.cvs.models import CVUpload


@dataclass
class AdminCVDownload:
    file_handle: object
    content_type: str
    filename: str


class AdminCVAccessService:
    @classmethod
    def prepare_download(cls, *, admin_user, public_id, metadata: dict | None = None) -> AdminCVDownload:
        if not getattr(admin_user, "is_superuser", False):
            raise PermissionDenied("Only a superuser can download private CV files.")

        cv_upload = get_object_or_404(CVUpload.all_objects, public_id=public_id)
        if not cv_upload.file:
            raise Http404("CV file not found.")

        # Open the file BEFORE writing the access log so a missing-file failure
        # does not produce a misleading successful "download" audit record.
        try:
            file_handle = cv_upload.file.open("rb")
        except FileNotFoundError as exc:
            raise Http404("CV file not found.") from exc

        # File opened successfully — safe to record the access.
        cls._log_access(admin_user=admin_user, public_id=cv_upload.public_id, metadata=metadata or {})

        content_type = cv_upload.mime_type or mimetypes.guess_type(cv_upload.original_filename)[0] or "application/pdf"
        return AdminCVDownload(
            file_handle=file_handle,
            content_type=content_type,
            filename=f"CV_{cv_upload.public_id}.pdf",
        )

    @staticmethod
    def _log_access(*, admin_user, public_id, metadata: dict) -> None:
        AdminFileAccessLog.objects.create(
            admin_user=admin_user,
            object_type="cv",
            object_public_id=public_id,
            action="download",
            reason=(metadata.get("reason") or "Admin CV review")[:255],
            ip_address=metadata.get("ip_address") or None,
            user_agent=metadata.get("user_agent", "")[:1000],
        )
