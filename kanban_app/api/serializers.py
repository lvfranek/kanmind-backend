from rest_framework import serializers
from django.contrib.auth.models import User
from kanban_app.models import Board


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
