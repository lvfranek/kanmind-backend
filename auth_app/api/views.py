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
    """Endpoint für User Registrierung - POST /api/registration/"""

    permission_classes = [AllowAny]

    def post(self, request):
        """Verarbeitet POST Request - erstellt neuen User und Token"""
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.save()
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Endpoint für User Login - POST /api/login/"""

    permission_classes = [AllowAny]

    def post(self, request):
        """Verarbeitet POST Request - authentifiziert User und gibt Token zurück"""
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)

            """Erstelle Response mit Token und User-Infos"""
            response_data = {
                'token': token.key,
                'fullname': user.profile.fullname,
                'email': user.email,
                'user_id': user.id
            }

            response_serializer = LoginResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
