from django.urls import path
from kanban_app.api.views import (
    BoardListCreateView,
    BoardDetailUpdateView,
    TaskListCreateView,
    TaskDetailUpdateDeleteView,
    TaskByReviewerView,
    CommentListCreateView,
    CommentDeleteView
)

urlpatterns = [
    path('boards/', BoardListCreateView.as_view(), name='board-list-create'),
    path('boards/<int:board_id>/', BoardDetailUpdateView.as_view(),
         name='board-detail-update'),
    path('tasks/', TaskListCreateView.as_view(), name='task-list-create'),
    path('tasks/reviewer/', TaskByReviewerView.as_view(), name='task-reviewer'),
    path('tasks/<int:task_id>/', TaskDetailUpdateDeleteView.as_view(),
         name='task-detail-update-delete'),
    path('tasks/<int:task_id>/comments/',
         CommentListCreateView.as_view(), name='comment-list-create'),
    path('tasks/<int:task_id>/comments/<int:comment_id>/',
         CommentDeleteView.as_view(), name='comment-delete'),
]
