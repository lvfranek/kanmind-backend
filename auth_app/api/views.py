from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from auth_app.api.serializers import (
    RegistrationSerializer,
    LoginSerializer,
    LoginResponseSerializer
)


class RegistrationView(APIView):
    """Endpoint for User Registration - POST /api/registration/"""

    permission_classes = [AllowAny]

    def post(self, request):
        """Handles POST request - creates a new User and Token"""
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.save()
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Endpoint for User Login - POST /api/login/"""

    permission_classes = [AllowAny]

    def post(self, request):
        """Handles POST request - authenticates the User and returns a token"""
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)

            """Build response with token and user info"""
            response_data = {
                'token': token.key,
                'fullname': user.profile.fullname,
                'email': user.email,
                'user_id': user.id
            }

            response_serializer = LoginResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
