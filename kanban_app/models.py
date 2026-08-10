from django.db import models
from django.contrib.auth.models import User


class Board(models.Model):
    """Kanban Board - gehört einem Owner und hat mehrere Members"""

    """Titel des Boards"""
    title = models.CharField(max_length=255)

    """User der das Board erstellt hat - ist der Owner"""
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="boards"
    )

    """Liste aller Members des Boards - können mehrere sein"""
    members = models.ManyToManyField(
        User,
        related_name="board_memberships"
    )

    """Wann wurde das Board erstellt"""
    created_at = models.DateTimeField(auto_now_add=True)

    """Wann wurde das Board zuletzt aktualisiert"""
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Board"
        verbose_name_plural = "Boards"
        ordering = ['-created_at']
