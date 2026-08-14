from django.urls import path

from kanban_app.api.views import (
    BoardListCreateView,
    BoardDetailUpdateDeleteView,
    TaskListCreateView,
    TaskDetailUpdateDeleteView,
    TaskAssignedToMeView,
    TaskByReviewerView,
    CommentListCreateView,
    CommentDeleteView,
    EmailCheckView
)

urlpatterns = [
    path('boards/', BoardListCreateView.as_view(), name='board-list-create'),
    path('boards/<int:board_id>/', BoardDetailUpdateDeleteView.as_view(),
         name='board-detail-update-delete'),
    path('tasks/', TaskListCreateView.as_view(), name='task-list-create'),
    path('tasks/assigned-to-me/', TaskAssignedToMeView.as_view(),
         name='task-assigned-to-me'),
    path('tasks/reviewing/', TaskByReviewerView.as_view(), name='task-reviewing'),
    path('tasks/<int:task_id>/', TaskDetailUpdateDeleteView.as_view(),
         name='task-detail-update-delete'),
    path('tasks/<int:task_id>/comments/',
         CommentListCreateView.as_view(), name='comment-list-create'),
    path('tasks/<int:task_id>/comments/<int:comment_id>/',
         CommentDeleteView.as_view(), name='comment-delete'),
    path('email-check/', EmailCheckView.as_view(), name='email-check'),
]
