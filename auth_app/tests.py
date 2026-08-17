import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from auth_app.models import UserProfile


@pytest.mark.django_db
class TestRegistration:
    """Tests for User Registration"""

    def setup_method(self):
        """Runs before every test"""
        self.client = APIClient()
        self.url = '/api/registration/'

    def test_registration_success(self):
        """Test: User can register successfully"""
        data = {
            'fullname': 'Max Mustermann',
            'email': 'max@example.com',
            'password': 'sicherespasswort123',
            'repeated_password': 'sicherespasswort123'
        }
        response = self.client.post(self.url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['token']
        assert response.data['user_id']
        assert User.objects.filter(email='max@example.com').exists()

    def test_registration_passwords_not_matching(self):
        """Test: Registration fails when passwords do not match"""
        data = {
            'fullname': 'Max Mustermann',
            'email': 'max@example.com',
            'password': 'sicherespasswort123',
            'repeated_password': 'anderes_passwort'
        }
        response = self.client.post(self.url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_registration_duplicate_email(self):
        """Test: Registration fails with duplicate email"""
        User.objects.create_user(
            username='existing@example.com',
            email='existing@example.com',
            password='password123'
        )

        data = {
            'fullname': 'Another User',
            'email': 'existing@example.com',
            'password': 'sicherespasswort123',
            'repeated_password': 'sicherespasswort123'
        }
        response = self.client.post(self.url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_registration_missing_fields(self):
        """Test: Registration fails when fields are missing"""
        data = {
            'fullname': 'Max Mustermann',
            'email': 'max@example.com'
        }
        response = self.client.post(self.url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLogin:
    """Tests for User Login"""

    def setup_method(self):
        """Runs before every test"""
        self.client = APIClient()
        self.url = '/api/login/'

        """Create test user"""
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpassword123'
        )
        UserProfile.objects.create(
            user=self.user,
            fullname='Test User'
        )

    def test_login_success(self):
        """Test: User can log in successfully"""
        data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        response = self.client.post(self.url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['token']
        assert response.data['user_id'] == self.user.id

    def test_login_wrong_password(self):
        """Test: Login fails with wrong password"""
        data = {
            'email': 'test@example.com',
            'password': 'falschespasswort'
        }
        response = self.client.post(self.url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_nonexistent_email(self):
        """Test: Login fails with a nonexistent email"""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'testpassword123'
        }
        response = self.client.post(self.url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
