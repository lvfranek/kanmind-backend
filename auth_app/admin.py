from django.contrib import admin
from auth_app.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin für UserProfile - zeigt fullname und User"""

    list_display = ["id", "fullname", "user"]
    search_fields = ["fullname", "user__email"]
    list_filter = ["user"]
    readonly_fields = ["user"]
