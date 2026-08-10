from rest_framework import serializers
from django.contrib.auth.models import User
from kanban_app.models import Board
from kanban_app.models import Board, Task, Comment


class UserSimpleSerializer(serializers.ModelSerializer):
    """Serializer für User - zeigt nur wichtige Felder"""

    class Meta:
        model = User
        fields = ["id", "email", "first_name"]


class BoardListSerializer(serializers.ModelSerializer):
    """Serializer für Board Liste - zeigt Overview mit Counts"""

    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()
    owner_id = serializers.IntegerField(source='owner.id', read_only=True)

    class Meta:
        model = Board
        fields = [
            "id", "title", "member_count", "ticket_count",
            "tasks_to_do_count", "tasks_high_prio_count", "owner_id"
        ]

    def get_member_count(self, obj):
        """Zählt alle Members des Boards"""
        return obj.members.count()

    def get_ticket_count(self, obj):
        """Platzhalter - wird später mit Tasks befüllt"""
        return 0

    def get_tasks_to_do_count(self, obj):
        """Platzhalter - wird später mit Tasks befüllt"""
        return 0

    def get_tasks_high_prio_count(self, obj):
        """Platzhalter - wird später mit Tasks befüllt"""
        return 0


class BoardDetailSerializer(serializers.ModelSerializer):
    """Serializer für Board Detail - zeigt Board mit allen Members"""

    members_data = serializers.SerializerMethodField()
    owner_data = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = ["id", "title", "owner_id", "owner_data", "members_data"]

    def get_members_data(self, obj):
        """Gibt alle Members als User Daten zurück"""
        members = obj.members.all()
        return UserSimpleSerializer(members, many=True).data

    def get_owner_data(self, obj):
        """Gibt Owner als User Daten zurück"""
        return UserSimpleSerializer(obj.owner).data


class BoardCreateUpdateSerializer(serializers.Serializer):
    """Serializer für Board erstellen und aktualisieren"""

    title = serializers.CharField(max_length=255, required=True)
    members = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )

    def validate_members(self, value):
        """Prüft ob alle Member-IDs existieren"""
        for member_id in value:
            if not User.objects.filter(id=member_id).exists():
                raise serializers.ValidationError(
                    f"User mit ID {member_id} existiert nicht."
                )
        return value

    def create(self, validated_data):
        """Erstellt neues Board mit Members"""
        user = self.context['request'].user
        board = Board.objects.create(
            title=validated_data['title'],
            owner=user
        )

        """Füge Members hinzu wenn vorhanden"""
        if 'members' in validated_data:
            members = User.objects.filter(id__in=validated_data['members'])
            board.members.set(members)

        return board

    def update(self, instance, validated_data):
        """Aktualisiert Board Titel und Members"""
        instance.title = validated_data.get('title', instance.title)
        instance.save()

        """Aktualisiere Members wenn vorhanden"""
        if 'members' in validated_data:
            members = User.objects.filter(id__in=validated_data['members'])
            instance.members.set(members)

        return instance


class UserSimpleSerializer(serializers.ModelSerializer):
    """Serializer für User - zeigt nur wichtige Felder"""

    class Meta:
        model = User
        fields = ["id", "email", "first_name"]


class CommentSerializer(serializers.ModelSerializer):
    """Serializer für Comments - zeigt Author als Name statt ID"""

    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["id", "created_at", "author", "content"]

    def get_author(self, obj):
        """Gibt Author Namen zurück"""
        return obj.author.first_name or obj.author.email


class TaskListSerializer(serializers.ModelSerializer):
    """Serializer für Task Liste - zeigt Task Overview"""

    assignee = UserSimpleSerializer(read_only=True)
    reviewer = UserSimpleSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id", "board", "title", "description", "status",
            "priority", "assignee", "reviewer", "due_date", "comments_count"
        ]

    def get_comments_count(self, obj):
        """Zählt Anzahl der Comments"""
        return obj.comments.count()


class TaskDetailSerializer(serializers.ModelSerializer):
    """Serializer für Task Detail - zeigt Task mit allen Comments"""

    assignee = UserSimpleSerializer(read_only=True)
    reviewer = UserSimpleSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id", "board", "title", "description", "status",
            "priority", "assignee", "reviewer", "due_date",
            "comments", "comments_count"
        ]

    def get_comments_count(self, obj):
        """Zählt Anzahl der Comments"""
        return obj.comments.count()


class TaskCreateUpdateSerializer(serializers.Serializer):
    """Serializer für Task erstellen und aktualisieren"""

    board = serializers.IntegerField(required=True)
    title = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(
        choices=['to-do', 'in-progress', 'review', 'done'],
        required=False
    )
    priority = serializers.ChoiceField(
        choices=['low', 'medium', 'high'],
        required=False
    )
    assignee_id = serializers.IntegerField(required=False, allow_null=True)
    reviewer_id = serializers.IntegerField(required=False, allow_null=True)
    due_date = serializers.DateField(required=False, allow_null=True)

    def validate_board(self, value):
        """Prüft ob Board existiert"""
        if not Board.objects.filter(id=value).exists():
            raise serializers.ValidationError("Board existiert nicht.")
        return value

    def validate_assignee_id(self, value):
        """Prüft ob Assignee existiert und Member des Boards ist"""
        if value is None:
            return value

        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("User existiert nicht.")
        return value

    def validate_reviewer_id(self, value):
        """Prüft ob Reviewer existiert und Member des Boards ist"""
        if value is None:
            return value

        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("User existiert nicht.")
        return value

    def create(self, validated_data):
        """Erstellt neue Task"""
        user = self.context['request'].user
        board = Board.objects.get(id=validated_data['board'])

        """Prüfe ob User Member des Boards ist"""
        if board.owner != user and user not in board.members.all():
            raise serializers.ValidationError(
                "Du bist kein Member dieses Boards."
            )

        task = Task.objects.create(
            board=board,
            title=validated_data['title'],
            description=validated_data.get('description', ''),
            status=validated_data.get('status', 'to-do'),
            priority=validated_data.get('priority', 'medium'),
            assignee_id=validated_data.get('assignee_id'),
            reviewer_id=validated_data.get('reviewer_id'),
            due_date=validated_data.get('due_date'),
            creator=user
        )

        return task

    def update(self, instance, validated_data):
        """Aktualisiert bestehende Task"""
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get(
            'description', instance.description)
        instance.status = validated_data.get('status', instance.status)
        instance.priority = validated_data.get('priority', instance.priority)
        instance.assignee_id = validated_data.get(
            'assignee_id', instance.assignee_id)
        instance.reviewer_id = validated_data.get(
            'reviewer_id', instance.reviewer_id)
        instance.due_date = validated_data.get('due_date', instance.due_date)
        instance.save()

        return instance
