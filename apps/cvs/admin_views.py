from django.http import FileResponse
from django.contrib.admin.views.decorators import staff_member_required
from apps.cvs.services.admin_access import AdminCVAccessService

@staff_member_required
def admin_cv_download(request, public_id):
    download = AdminCVAccessService.prepare_download(
        admin_user=request.user,
        public_id=public_id,
        metadata={
            "reason": request.GET.get("reason", "Admin CV review"),
            "ip_address": request.META.get("REMOTE_ADDR"),
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
        },
    )
    response = FileResponse(download.file_handle, content_type=download.content_type, as_attachment=True)
    response["Content-Disposition"] = f'attachment; filename="{download.filename}"'
    return response
