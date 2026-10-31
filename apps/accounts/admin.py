from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "display_name", "role", "batch", "is_active", "last_login")
    list_filter = ("role", "is_active", "batch")
    search_fields = ("username", "display_name", "email", "phone")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Chayabari", {"fields": ("role", "batch", "display_name", "bio", "phone", "avatar", "must_change_password")}),
    )
