from rest_framework import serializers
from django.contrib.auth.models import User
from kanban_app.models import Board, Task, Comment


def get_user_fullname(user):
    """Returns fullname from Profile, with email as fallback without a Profile"""
    profile = getattr(user, 'profile', None)
    return profile.fullname if profile else user.email


class UserSimpleSerializer(serializers.ModelSerializer):
    """Serializer for User - shows only important fields"""

    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "fullname"]

    def get_fullname(self, obj):
        """Returns the fullname of the User"""
        return get_user_fullname(obj)


class BoardListSerializer(serializers.ModelSerializer):
    """Serializer for Board list - shows overview with counts"""

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
        """Counts all members of the Board"""
        return obj.members.count()

    def get_ticket_count(self, obj):
        """Counts all tasks of the Board"""
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        """Counts tasks with status to-do"""
        return obj.tasks.filter(status='to-do').count()

    def get_tasks_high_prio_count(self, obj):
        """Counts tasks with priority high"""
        return obj.tasks.filter(priority='high').count()


class BoardDetailSerializer(serializers.ModelSerializer):
    """Serializer for Board detail GET - shows Board with members and tasks"""

    owner_id = serializers.IntegerField(source='owner.id', read_only=True)
    members = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = ["id", "title", "owner_id", "members", "tasks"]

    def get_members(self, obj):
        """Returns all members as User data"""
        return UserSimpleSerializer(obj.members.all(), many=True).data

    def get_tasks(self, obj):
        """Returns all tasks of the Board"""
        return TaskNestedSerializer(obj.tasks.all(), many=True).data


class BoardUpdateResponseSerializer(serializers.ModelSerializer):
    """Serializer for Board PATCH response - shows Owner and Members nested"""

    owner_data = serializers.SerializerMethodField()
    members_data = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = ["id", "title", "owner_data", "members_data"]

    def get_owner_data(self, obj):
        """Returns Owner as User data"""
        return UserSimpleSerializer(obj.owner).data

    def get_members_data(self, obj):
        """Returns all members as User data"""
        return UserSimpleSerializer(obj.members.all(), many=True).data


class BoardCreateUpdateSerializer(serializers.Serializer):
    """Serializer for creating and updating a Board"""

    title = serializers.CharField(max_length=255, required=True)
    members = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )

    def validate_members(self, value):
        """Checks that all member IDs exist"""
        for member_id in value:
            if not User.objects.filter(id=member_id).exists():
                raise serializers.ValidationError(
                    f"User with ID {member_id} does not exist."
                )
        return value

    def create(self, validated_data):
        """Creates a new Board with members"""
        user = self.context['request'].user
        board = Board.objects.create(
            title=validated_data['title'],
            owner=user
        )

        """Add members if provided"""
        if 'members' in validated_data:
            members = User.objects.filter(id__in=validated_data['members'])
            board.members.set(members)

        return board

    def update(self, instance, validated_data):
        """Updates Board title and members"""
        instance.title = validated_data.get('title', instance.title)
        instance.save()

        """Update members if provided"""
        if 'members' in validated_data:
            members = User.objects.filter(id__in=validated_data['members'])
            instance.members.set(members)

        return instance


class EmailCheckSerializer(serializers.Serializer):
    """Serializer for Email-Check - validates the email query parameter"""

    email = serializers.EmailField(required=True)


class EmailCheckResponseSerializer(serializers.Serializer):
    """Serializer for Email-Check response - formats the User data"""

    id = serializers.IntegerField()
    email = serializers.EmailField()
    fullname = serializers.CharField()


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for Comments - shows Author as name instead of ID"""

    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["id", "created_at", "author", "content"]

    def get_author(self, obj):
        """Returns the Author's name"""
        return get_user_fullname(obj.author)


class TaskListSerializer(serializers.ModelSerializer):
    """Serializer for Task list - shows Task overview"""

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
        """Counts the number of Comments"""
        return obj.comments.count()


class TaskDetailSerializer(serializers.ModelSerializer):
    """Serializer for Task detail - shows Task with all Comments"""

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
        """Counts the number of Comments"""
        return obj.comments.count()


class TaskNestedSerializer(serializers.ModelSerializer):
    """Serializer for Tasks nested in Board detail - without board field"""

    assignee = UserSimpleSerializer(read_only=True)
    reviewer = UserSimpleSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id", "title", "description", "status",
            "priority", "assignee", "reviewer", "due_date", "comments_count"
        ]

    def get_comments_count(self, obj):
        """Counts the number of Comments"""
        return obj.comments.count()


class TaskUpdateResponseSerializer(serializers.ModelSerializer):
    """Serializer for Task PATCH response - without board and comments_count"""

    assignee = UserSimpleSerializer(read_only=True)
    reviewer = UserSimpleSerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            "id", "title", "description", "status",
            "priority", "assignee", "reviewer", "due_date"
        ]


class TaskCreateUpdateSerializer(serializers.Serializer):
    """Serializer for creating and updating a Task"""

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
        """Checks that the Board exists"""
        if not Board.objects.filter(id=value).exists():
            raise serializers.ValidationError("Board does not exist.")
        return value

    def validate_assignee_id(self, value):
        """Checks that the Assignee exists and is a Member of the Board"""
        if value is None:
            return value

        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("User does not exist.")
        return value

    def validate_reviewer_id(self, value):
        """Checks that the Reviewer exists and is a Member of the Board"""
        if value is None:
            return value

        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("User does not exist.")
        return value

    def create(self, validated_data):
        """Creates a new Task"""
        user = self.context['request'].user
        board = Board.objects.get(id=validated_data['board'])
        self._check_board_membership(board, user)
        return self._create_task(board, user, validated_data)

    def _check_board_membership(self, board, user):
        """Checks that the User is a Member of the Board"""
        if board.owner != user and user not in board.members.all():
            raise serializers.ValidationError(
                "You are not a member of this board."
            )

    def _create_task(self, board, user, validated_data):
        """Creates the Task with the validated data"""
        return Task.objects.create(
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

    def update(self, instance, validated_data):
        """Updates the existing Task"""
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
