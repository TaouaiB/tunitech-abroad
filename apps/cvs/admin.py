from django.contrib import admin
from .models import CVUpload, CVParsedData

@admin.register(CVUpload)
class CVUploadAdmin(admin.ModelAdmin):
    list_display = ("user", "original_filename", "is_active", "parse_status", "uploaded_at", "deleted_at")
    list_filter = ("is_active", "parse_status", "text_extraction_status")
    search_fields = ("user__email", "original_filename", "public_id")
    readonly_fields = ("public_id", "uploaded_at", "parsed_at", "deleted_at", "file_hash", "file_size", "mime_type")
    exclude = ("file",)

    def get_queryset(self, request):
        return self.model.all_objects.get_queryset()

    def has_add_permission(self, request):
        return False

@admin.register(CVParsedData)
class CVParsedDataAdmin(admin.ModelAdmin):
    list_display = ('cv_upload', 'extraction_method', 'extracted_name', 'extracted_email', 'created_at')
    list_filter = ('extraction_method',)
    search_fields = ('cv_upload__user__email', 'extracted_name', 'extracted_email')
    readonly_fields = ('cv_upload', 'created_at', 'updated_at', 'deterministic_json', 'llm_json', 'merged_json', 'confidence_json', 'warnings_json')
    exclude = ('raw_text',)
