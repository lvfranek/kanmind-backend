from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from auth_app.models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile - converts model data to JSON"""

    class Meta:
        model = UserProfile
        fields = ["id", "fullname"]


class RegistrationSerializer(serializers.Serializer):
    """Serializer for Registration - validates incoming registration data"""

    fullname = serializers.CharField(max_length=255, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, min_length=6)
    repeated_password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs):
        """Checks that both passwords match"""
        if attrs['password'] != attrs['repeated_password']:
            raise serializers.ValidationError(
                {"password": "Passwords do not match."}
            )
        return attrs

    def validate_email(self, value):
        """Checks that the email is not already registered"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "This email is already registered.")
        return value

    def create(self, validated_data):
        """Creates a new User, UserProfile and Token"""
        user = self._create_user(validated_data)
        profile = self._create_profile(user, validated_data)
        token = self._create_token(user)
        return self._build_response(user, profile, token)

    def _create_user(self, validated_data):
        """Creates the User with email as username"""
        return User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password']
        )

    def _create_profile(self, user, validated_data):
        """Creates the UserProfile for the User"""
        return UserProfile.objects.create(
            user=user,
            fullname=validated_data['fullname']
        )

    def _create_token(self, user):
        """Creates or fetches the Auth token of the User"""
        token, created = Token.objects.get_or_create(user=user)
        return token

    def _build_response(self, user, profile, token):
        """Builds the response dict for the Registration"""
        return {
            'token': token.key,
            'fullname': profile.fullname,
            'email': user.email,
            'user_id': user.id
        }


class LoginSerializer(serializers.Serializer):
    """Serializer for Login - validates email and password"""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Checks that the User exists and the password is correct"""
        email = attrs.get('email')
        password = attrs.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"email": "Email not found."}
            )

        if not user.check_password(password):
            raise serializers.ValidationError(
                {"password": "Password is incorrect."}
            )

        attrs['user'] = user
        return attrs


class LoginResponseSerializer(serializers.Serializer):
    """Serializer for Login Response - formats the response"""

    token = serializers.CharField()
    fullname = serializers.CharField()
    email = serializers.EmailField()
    user_id = serializers.IntegerField()
