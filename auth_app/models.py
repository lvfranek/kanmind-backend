from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """Extends the Django User with an additional fullname field"""

    """1:1 relation to User - deleted when the User is deleted"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    """Stores the full name"""
    fullname = models.CharField(max_length=255)

    """String representation in Admin and logs"""
    def __str__(self):
        return self.fullname

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
