from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """Erweitert Django User mit zusätzlichem fullname Feld"""

    """1:1 Verbindung zu User - wird gelöscht wenn User gelöscht wird"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    """Speichert den vollständigen Namen"""
    fullname = models.CharField(max_length=255)

    """String-Darstellung in Admin und Logs"""
    def __str__(self):
        return self.fullname

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
