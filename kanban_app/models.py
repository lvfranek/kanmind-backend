from django.db import models
from django.contrib.auth.models import User


class Board(models.Model):
    """Kanban Board - belongs to an Owner and has multiple Members"""

    """Title of the Board"""
    title = models.CharField(max_length=255)

    """User who created the Board - is the Owner"""
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="boards"
    )

    """List of all Members of the Board - can be several"""
    members = models.ManyToManyField(
        User,
        related_name="board_memberships"
    )

    """When was the Board created"""
    created_at = models.DateTimeField(auto_now_add=True)

    """When was the Board last updated"""
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Board"
        verbose_name_plural = "Boards"
        ordering = ['-created_at']


class Task(models.Model):
    """Task belongs to a Board - has Status, Priority, Assignee and Reviewer"""

    STATUS_CHOICES = [
        ('to-do', 'To Do'),
        ('in-progress', 'In Progress'),
        ('review', 'Review'),
        ('done', 'Done'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    """The Board this Task belongs to"""
    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        related_name="tasks"
    )

    """Title of the Task"""
    title = models.CharField(max_length=255)

    """Description of the Task"""
    description = models.TextField(blank=True, null=True)

    """Status of the Task - to-do, in-progress, review or done"""
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='to-do'
    )

    """Priority of the Task - low, medium or high"""
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )

    """User the Task is assigned to"""
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks"
    )

    """User who reviews the Task"""
    reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_tasks"
    )

    """Due date of the Task"""
    due_date = models.DateField(blank=True, null=True)

    """Who created the Task"""
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_tasks"
    )

    """When was the Task created"""
    created_at = models.DateTimeField(auto_now_add=True)

    """When was the Task last updated"""
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ['-created_at']


class Comment(models.Model):
    """Comment on a Task - created by a User"""

    """The Task this Comment belongs to"""
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="comments"
    )

    """The content of the Comment"""
    content = models.TextField()

    """The Author of the Comment"""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments"
    )

    """When was the Comment created"""
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author} on {self.task}"

    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ['created_at']
