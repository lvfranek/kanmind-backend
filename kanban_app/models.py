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


class Task(models.Model):
    """Task gehört zu einem Board - hat Status, Priorität, Assignee und Reviewer"""

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

    """Das Board zu dem die Task gehört"""
    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        related_name="tasks"
    )

    """Titel der Task"""
    title = models.CharField(max_length=255)

    """Beschreibung der Task"""
    description = models.TextField(blank=True, null=True)

    """Status der Task - to-do, in-progress, review oder done"""
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='to-do'
    )

    """Priorität der Task - low, medium oder high"""
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )

    """User dem die Task zugewiesen ist"""
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks"
    )

    """User der die Task reviewed"""
    reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_tasks"
    )

    """Fälligkeitsdatum der Task"""
    due_date = models.DateField(blank=True, null=True)

    """Wer hat die Task erstellt"""
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_tasks"
    )

    """Wann wurde die Task erstellt"""
    created_at = models.DateTimeField(auto_now_add=True)

    """Wann wurde die Task zuletzt aktualisiert"""
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ['-created_at']


class Comment(models.Model):
    """Kommentar zu einer Task - wird von einem User erstellt"""

    """Die Task zu der der Kommentar gehört"""
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="comments"
    )

    """Der Inhalt des Kommentars"""
    content = models.TextField()

    """Der Author des Kommentars"""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments"
    )

    """Wann wurde der Kommentar erstellt"""
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Kommentar von {self.author} zu {self.task}"

    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ['created_at']
