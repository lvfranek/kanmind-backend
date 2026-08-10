from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from auth_app.models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer für UserProfile - konvertiert Modeldaten zu JSON"""

    class Meta:
        model = UserProfile
        fields = ["id", "fullname"]


class RegistrationSerializer(serializers.Serializer):
    """Serializer für Registration - validiert eingehende Registrierungsdaten"""

    fullname = serializers.CharField(max_length=255, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, min_length=6)
    repeated_password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs):
        """Prüft ob beide Passwörter identisch sind"""
        if attrs['password'] != attrs['repeated_password']:
            raise serializers.ValidationError(
                {"password": "Passwörter stimmen nicht überein."}
            )
        return attrs

    def validate_email(self, value):
        """Prüft ob Email bereits existiert"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Diese Email ist bereits registriert.")
        return value

    def create(self, validated_data):
        """Erstellt neuen User, UserProfile und Token"""
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password']
        )

        profile = UserProfile.objects.create(
            user=user,
            fullname=validated_data['fullname']
        )

        token, created = Token.objects.get_or_create(user=user)

        return {
            'token': token.key,
            'fullname': profile.fullname,
            'email': user.email,
            'user_id': user.id
        }


class LoginSerializer(serializers.Serializer):
    """Serializer für Login - validiert Email und Passwort"""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Prüft ob User existiert und Passwort korrekt ist"""
        email = attrs.get('email')
        password = attrs.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"email": "Email nicht gefunden."}
            )

        if not user.check_password(password):
            raise serializers.ValidationError(
                {"password": "Passwort ist falsch."}
            )

        attrs['user'] = user
        return attrs


class LoginResponseSerializer(serializers.Serializer):
    """Serializer für Login Response - formatiert die Antwort"""

    token = serializers.CharField()
    fullname = serializers.CharField()
    email = serializers.EmailField()
    user_id = serializers.IntegerField()
