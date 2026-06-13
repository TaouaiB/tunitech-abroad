from django.contrib import admin
from .models import UserEvent

@admin.register(UserEvent)
class UserEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'user', 'created_at')
    search_fields = ('event_type', 'user__email')
    list_filter = ('event_type', 'created_at')
    readonly_fields = ('created_at',)
