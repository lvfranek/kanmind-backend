from django.contrib import admin
from kanban_app.models import Board, Task, Comment


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    """Admin für Board - zeigt Titel, Owner und Members"""

    list_display = ["id", "title", "owner", "get_member_count"]
    search_fields = ["title", "owner__email"]
    list_filter = ["created_at", "owner"]
    filter_horizontal = ["members"]
    readonly_fields = ["created_at", "updated_at"]

    def get_member_count(self, obj):
        """Zeigt Anzahl Members"""
        return obj.members.count()
    get_member_count.short_description = "Members"


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin für Task - zeigt Title, Status, Priority, Board"""

    list_display = ["id", "title", "board",
                    "status", "priority", "assignee", "reviewer"]
    search_fields = ["title", "board__title"]
    list_filter = ["status", "priority", "board", "created_at"]
    readonly_fields = ["created_at", "updated_at", "creator"]

    fieldsets = (
        ("Task Infos", {
            "fields": ("board", "title", "description")
        }),
        ("Status & Priorität", {
            "fields": ("status", "priority")
        }),
        ("Zuweisungen", {
            "fields": ("assignee", "reviewer", "creator")
        }),
        ("Wichtige Daten", {
            "fields": ("due_date", "created_at", "updated_at")
        }),
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin für Comment - zeigt Content, Author, Task"""

    list_display = ["id", "author", "task", "created_at"]
    search_fields = ["content", "author__email", "task__title"]
    list_filter = ["created_at", "author"]
    readonly_fields = ["created_at", "author"]

    def save_model(self, request, obj, form, change):
        """Setzt Author automatisch auf den aktuellen User"""
        if not change:
            obj.author = request.user
        super().save_model(request, obj, form, change)
