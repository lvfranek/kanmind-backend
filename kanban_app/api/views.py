from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from kanban_app.api.serializers import (
    BoardListSerializer,
    BoardDetailSerializer,
    BoardUpdateResponseSerializer,
    BoardCreateUpdateSerializer,
    TaskListSerializer,
    TaskDetailSerializer,
    TaskUpdateResponseSerializer,
    TaskCreateUpdateSerializer,
    CommentSerializer,
    EmailCheckSerializer,
    EmailCheckResponseSerializer,
    get_user_fullname
)
from kanban_app.models import Board, Task, Comment


class BoardListCreateView(APIView):
    """Endpoint for Board list (GET) and create (POST) - /api/boards/"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Returns all Boards where the User is Owner or Member"""
        boards = Board.objects.filter(
            Q(owner=request.user) | Q(members=request.user)
        ).distinct()

        serializer = BoardListSerializer(boards, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Creates a new Board - User automatically becomes Owner"""
        serializer = BoardCreateUpdateSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            board = serializer.save()
            response_serializer = BoardListSerializer(board)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BoardDetailUpdateDeleteView(APIView):
    """Endpoint for Board detail (GET), update (PATCH) and delete - /api/boards/{board_id}/"""

    permission_classes = [IsAuthenticated]

    def get_board(self, board_id, user):
        """Checks whether the User has access to the Board"""
        board = get_object_or_404(Board, id=board_id)

        """Check whether the User is Owner or Member"""
        if board.owner != user and user not in board.members.all():
            return None

        return board

    def get(self, request, board_id):
        """Returns Board detail with all Members"""
        board = self.get_board(board_id, request.user)

        if not board:
            return Response(
                {"detail": "Board not found or no access."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = BoardDetailSerializer(board)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, board_id):
        """Updates Board title and members"""
        board = self.get_board(board_id, request.user)

        if not board:
            return Response(
                {"detail": "Board not found or no access."},
                status=status.HTTP_403_FORBIDDEN
            )

        permission_error = self._check_update_permission(board, request.user)
        if permission_error:
            return permission_error

        return self._save_board(board, request)

    def _check_update_permission(self, board, user):
        """Checks whether the User is Owner or Member, otherwise returns an error response"""
        if board.owner != user and user not in board.members.all():
            return Response(
                {"detail": "No permission to update this board."},
                status=status.HTTP_403_FORBIDDEN
            )
        return None

    def _save_board(self, board, request):
        """Validates and saves the Board changes"""
        serializer = BoardCreateUpdateSerializer(
            board,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            updated_board = serializer.save()
            response_serializer = BoardUpdateResponseSerializer(updated_board)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, board_id):
        """Deletes the Board completely - only the Owner may do this"""
        board = get_object_or_404(Board, id=board_id)

        if board.owner != request.user:
            return Response(
                {"detail": "Only the Owner may delete this board."},
                status=status.HTTP_403_FORBIDDEN
            )

        board.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TaskListCreateView(APIView):
    """Endpoint for a Board's Tasks (GET) and Task create (POST) - /api/tasks/"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Returns all Tasks of the authenticated User"""
        tasks = Task.objects.filter(
            board__members=request.user
        ) | Task.objects.filter(
            board__owner=request.user
        )

        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Creates a new Task in the Board"""
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
    """Endpoint for Task detail (GET), update (PATCH) and delete - /api/tasks/{task_id}/"""

    permission_classes = [IsAuthenticated]

    def get_task(self, task_id, user):
        """Checks whether the User has access to the Task"""
        task = get_object_or_404(Task, id=task_id)
        board = task.board

        """Check whether the User is Member or Owner of the Board"""
        if board.owner != user and user not in board.members.all():
            return None

        return task

    def get(self, request, task_id):
        """Returns Task details with Comments"""
        task = self.get_task(task_id, request.user)

        if not task:
            return Response(
                {"detail": "Task not found or no access."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = TaskDetailSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, task_id):
        """Updates a Task - only Board Members may do this"""
        task = self.get_task(task_id, request.user)

        if not task:
            return Response(
                {"detail": "Task not found or no access."},
                status=status.HTTP_403_FORBIDDEN
            )

        return self._save_task(task, request)

    def _save_task(self, task, request):
        """Validates and saves the Task changes"""
        serializer = TaskCreateUpdateSerializer(
            task,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            updated_task = serializer.save()
            response_serializer = TaskUpdateResponseSerializer(updated_task)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, task_id):
        """Deletes a Task - only the Task Creator or Board Owner may do this"""
        task = self.get_task(task_id, request.user)

        if not task:
            return Response(
                {"detail": "Task not found or no access."},
                status=status.HTTP_403_FORBIDDEN
            )

        """Only the Creator or Board Owner may delete"""
        if task.creator != request.user and task.board.owner != request.user:
            return Response(
                {"detail": "No permission to delete this task."},
                status=status.HTTP_403_FORBIDDEN
            )

        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TaskAssignedToMeView(APIView):
    """Endpoint for Tasks where the User is Assignee - /api/tasks/assigned-to-me/"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Returns all Tasks where the User is set as Assignee"""
        tasks = Task.objects.filter(assignee=request.user)

        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TaskByReviewerView(APIView):
    """Endpoint for Tasks where the User is Reviewer - /api/tasks/reviewing/"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Returns all Tasks where the User is set as Reviewer"""
        tasks = Task.objects.filter(reviewer=request.user)

        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CommentListCreateView(APIView):
    """Endpoint for a Task's Comments - /api/tasks/{task_id}/comments/"""

    permission_classes = [IsAuthenticated]

    def get_task(self, task_id, user):
        """Checks whether the User has access to the Task"""
        task = get_object_or_404(Task, id=task_id)
        board = task.board

        """Check whether the User is Member or Owner of the Board"""
        if board.owner != user and user not in board.members.all():
            return None

        return task

    def get(self, request, task_id):
        """Returns all Comments of the Task"""
        task = self.get_task(task_id, request.user)

        if not task:
            return Response(
                {"detail": "Task not found or no access."},
                status=status.HTTP_403_FORBIDDEN
            )

        comments = task.comments.all()
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, task_id):
        """Creates a new Comment for the Task"""
        task = self.get_task(task_id, request.user)

        if not task:
            return Response(
                {"detail": "Task not found or no access."},
                status=status.HTTP_403_FORBIDDEN
            )

        validation_error = self._validate_content(request)
        if validation_error:
            return validation_error

        return self._create_comment(task, request)

    def _validate_content(self, request):
        """Checks whether content is present in the body, otherwise returns an error response"""
        if 'content' not in request.data or not request.data['content']:
            return Response(
                {"content": "This field is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return None

    def _create_comment(self, task, request):
        """Creates the Comment and returns the response"""
        comment = Comment.objects.create(
            task=task,
            content=request.data['content'],
            author=request.user
        )

        serializer = CommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CommentDeleteView(APIView):
    """Endpoint for deleting a Comment - /api/tasks/{task_id}/comments/{comment_id}/"""

    permission_classes = [IsAuthenticated]

    def get_comment(self, task_id, comment_id, user):
        """Checks whether the User has access to the Comment"""
        task = get_object_or_404(Task, id=task_id)
        comment = get_object_or_404(Comment, id=comment_id, task=task)
        board = task.board

        """Check whether the User is Member or Owner of the Board"""
        if board.owner != user and user not in board.members.all():
            return None

        return comment

    def delete(self, request, task_id, comment_id):
        """Deletes a Comment - only the Comment Author may do this"""
        comment = self.get_comment(task_id, comment_id, request.user)

        if not comment:
            return Response(
                {"detail": "Comment not found or no access."},
                status=status.HTTP_403_FORBIDDEN
            )

        """Only the Author may delete the Comment"""
        if comment.author != request.user:
            return Response(
                {"detail": "No permission to delete this comment."},
                status=status.HTTP_403_FORBIDDEN
            )

        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmailCheckView(APIView):
    """Endpoint checks whether a User with the given email exists - /api/email-check/"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Validates the email query parameter and looks up the matching User"""
        serializer = EmailCheckSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        return self._find_user(email)

    def _find_user(self, email):
        """Looks up the User by email and returns the matching response"""
        user = User.objects.filter(email=email).first()
        if not user:
            return Response(
                {"detail": "No user found with this email."},
                status=status.HTTP_404_NOT_FOUND
            )

        data = {"id": user.id, "email": user.email, "fullname": get_user_fullname(user)}
        response_serializer = EmailCheckResponseSerializer(data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
