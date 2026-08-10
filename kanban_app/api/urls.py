from django.urls import path
from kanban_app.api.views import (
    BoardListCreateView,
    BoardDetailUpdateView
)

urlpatterns = [
    path('boards/', BoardListCreateView.as_view(), name='board-list-create'),
    path('boards/<int:board_id>/', BoardDetailUpdateView.as_view(),
         name='board-detail-update'),
]
