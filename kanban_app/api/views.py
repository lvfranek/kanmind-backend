from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from kanban_app.models import Board
from kanban_app.api.serializers import (
    BoardListSerializer,
    BoardDetailSerializer,
    BoardCreateUpdateSerializer
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
