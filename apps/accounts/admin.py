from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(DefaultUserAdmin):
    list_display = ("email", "username", "is_staff", "is_active", "date_joined", "last_login")
    search_fields = ("email", "username")
    list_filter = ("is_active", "is_staff", "is_superuser", "date_joined", "last_login")
    readonly_fields = ("date_joined", "last_login")
    ordering = ("email",)
