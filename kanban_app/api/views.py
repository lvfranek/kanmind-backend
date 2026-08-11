from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from kanban_app.models import Board, Task, Comment
from kanban_app.api.serializers import (
    BoardListSerializer,
    BoardDetailSerializer,
    BoardCreateUpdateSerializer,
    TaskListSerializer,
    TaskDetailSerializer,
    TaskCreateUpdateSerializer,
    CommentSerializer
)


class BoardListCreateView(APIView):
    """Endpoint für Board Liste (GET) und erstellen (POST) - /api/boards/"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Gibt alle Boards zurück wo User Owner oder Member ist"""
        boards = Board.objects.filter(
            Q(owner=request.user) | Q(members=request.user)
        ).distinct()

        serializer = BoardListSerializer(boards, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Erstellt neues Board - User wird automatisch Owner"""
        serializer = BoardCreateUpdateSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            board = serializer.save()
            response_serializer = BoardListSerializer(board)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BoardDetailUpdateView(APIView):
    """Endpoint für Board Detail (GET) und Update (PATCH) - /api/boards/{board_id}/"""

    permission_classes = [IsAuthenticated]

    def get_board(self, board_id, user):
        """Prüft ob User Zugriff auf Board hat"""
        board = get_object_or_404(Board, id=board_id)

        """Prüfe ob User Owner oder Member ist"""
        if board.owner != user and user not in board.members.all():
            return None

        return board

    def get(self, request, board_id):
        """Gibt Board Detail mit allen Members zurück"""
        board = self.get_board(board_id, request.user)

        if not board:
            return Response(
                {"detail": "Board nicht gefunden oder kein Zugriff."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = BoardDetailSerializer(board)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, board_id):
        """Aktualisiert Board Titel und Members"""
        board = self.get_board(board_id, request.user)

        if not board:
            return Response(
                {"detail": "Board nicht gefunden oder kein Zugriff."},
                status=status.HTTP_403_FORBIDDEN
            )

        """Prüfe ob User Owner oder Member ist"""
        if board.owner != request.user and request.user not in board.members.all():
            return Response(
                {"detail": "Keine Berechtigung dieses Board zu aktualisieren."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = BoardCreateUpdateSerializer(
            board,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            updated_board = serializer.save()
            response_serializer = BoardDetailSerializer(updated_board)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskListCreateView(APIView):
    """Endpoint für Tasks eines Boards (GET) und Task erstellen (POST) - /api/tasks/"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Gibt alle Tasks des authentifizierten Users zurück"""
        tasks = Task.objects.filter(
            board__members=request.user
        ) | Task.objects.filter(
            board__owner=request.user
        )

        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Erstellt neue Task im Board"""
        serializer = TaskCreateUpdateSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            task = serializer.save()
            response_serializer = TaskListSerializer(task)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskDetailUpdateDeleteView(APIView):
    """Endpoint für Task Detail (GET), Update (PATCH) und Delete - /api/tasks/{task_id}/"""

    permission_classes = [IsAuthenticated]

    def get_task(self, task_id, user):
        """Prüft ob User Zugriff auf Task hat"""
        task = get_object_or_404(Task, id=task_id)
        board = task.board

        """Prüfe ob User Member oder Owner des Boards ist"""
        if board.owner != user and user not in board.members.all():
            return None

        return task

    def get(self, request, task_id):
        """Gibt Task Details mit Comments zurück"""
        task = self.get_task(task_id, request.user)

        if not task:
            return Response(
                {"detail": "Task nicht gefunden oder kein Zugriff."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = TaskDetailSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, task_id):
        """Aktualisiert Task - nur Board Member dürfen das"""
        task = self.get_task(task_id, request.user)

        if not task:
            return Response(
                {"detail": "Task nicht gefunden oder kein Zugriff."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = TaskCreateUpdateSerializer(
            task,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            updated_task = serializer.save()
            response_serializer = TaskListSerializer(updated_task)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, task_id):
        """Löscht Task - nur Task Creator oder Board Owner dürfen das"""
        task = self.get_task(task_id, request.user)

        if not task:
            return Response(
                {"detail": "Task nicht gefunden oder kein Zugriff."},
                status=status.HTTP_403_FORBIDDEN
            )

        """Nur Creator oder Board Owner dürfen löschen"""
        if task.creator != request.user and task.board.owner != request.user:
            return Response(
                {"detail": "Keine Berechtigung diese Task zu löschen."},
                status=status.HTTP_403_FORBIDDEN
            )

        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TaskByReviewerView(APIView):
    """Endpoint für Tasks wo User Reviewer ist - /api/tasks/reviewer/"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Gibt alle Tasks zurück wo User als Reviewer eingetragen ist"""
        tasks = Task.objects.filter(reviewer=request.user)

        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CommentListCreateView(APIView):
    """Endpoint für Comments einer Task - /api/tasks/{task_id}/comments/"""

    permission_classes = [IsAuthenticated]

    def get_task(self, task_id, user):
        """Prüft ob User Zugriff auf Task hat"""
        task = get_object_or_404(Task, id=task_id)
        board = task.board

        """Prüfe ob User Member oder Owner des Boards ist"""
        if board.owner != user and user not in board.members.all():
            return None

        return task

    def get(self, request, task_id):
        """Gibt alle Comments der Task zurück"""
        task = self.get_task(task_id, request.user)

        if not task:
            return Response(
                {"detail": "Task nicht gefunden oder kein Zugriff."},
                status=status.HTTP_403_FORBIDDEN
            )

        comments = task.comments.all()
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, task_id):
        """Erstellt neuen Comment für die Task"""
        task = self.get_task(task_id, request.user)

        if not task:
            return Response(
                {"detail": "Task nicht gefunden oder kein Zugriff."},
                status=status.HTTP_403_FORBIDDEN
            )

        """Prüfe ob content im Body ist"""
        if 'content' not in request.data or not request.data['content']:
            return Response(
                {"content": "Dieses Feld ist erforderlich."},
                status=status.HTTP_400_BAD_REQUEST
            )

        comment = Comment.objects.create(
            task=task,
            content=request.data['content'],
            author=request.user
        )

        serializer = CommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CommentDeleteView(APIView):
    """Endpoint zum Löschen eines Comments - /api/tasks/{task_id}/comments/{comment_id}/"""

    permission_classes = [IsAuthenticated]

    def get_comment(self, task_id, comment_id, user):
        """Prüft ob User Zugriff auf Comment hat"""
        task = get_object_or_404(Task, id=task_id)
        comment = get_object_or_404(Comment, id=comment_id, task=task)
        board = task.board

        """Prüfe ob User Member oder Owner des Boards ist"""
        if board.owner != user and user not in board.members.all():
            return None

        return comment

    def delete(self, request, task_id, comment_id):
        """Löscht Comment - nur Comment Author darf das"""
        comment = self.get_comment(task_id, comment_id, request.user)

        if not comment:
            return Response(
                {"detail": "Comment nicht gefunden oder kein Zugriff."},
                status=status.HTTP_403_FORBIDDEN
            )

        """Nur Author darf Comment löschen"""
        if comment.author != request.user:
            return Response(
                {"detail": "Keine Berechtigung diesen Comment zu löschen."},
                status=status.HTTP_403_FORBIDDEN
            )

        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
