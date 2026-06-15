from django.contrib import admin
from .models import LLMRequestLog

@admin.register(LLMRequestLog)
class LLMRequestLogAdmin(admin.ModelAdmin):
    list_display = ("purpose", "model_name", "status", "user", "created_at")
    list_filter = ("status", "purpose", "provider")
    search_fields = ("user__email", "purpose", "model_name")
    readonly_fields = ("created_at",)
