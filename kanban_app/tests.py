import pytest
from django.contrib.auth.models import User

from rest_framework.test import APIClient
from rest_framework import status

from auth_app.models import UserProfile
from kanban_app.models import Board, Task, Comment


@pytest.mark.django_db
class TestBoards:
    """Tests für Board CRUD Operationen"""

    def setup_method(self):
        """Erstellt Test User und authentifizierten Client"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='owner@example.com',
            email='owner@example.com',
            password='password123'
        )
        self.other_user = User.objects.create_user(
            username='other@example.com',
            email='other@example.com',
            password='password123'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_board_success(self):
        """Test: Board wird erfolgreich erstellt"""
        data = {'title': 'Mein Board', 'members': []}
        response = self.client.post('/api/boards/', data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'Mein Board'
        assert response.data['owner_id'] == self.user.id

    def test_create_board_unauthenticated(self):
        """Test: Board erstellen schlägt fehl ohne Authentication"""
        self.client.force_authenticate(user=None)
        data = {'title': 'Mein Board'}
        response = self.client.post('/api/boards/', data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_boards(self):
        """Test: User sieht nur eigene Boards"""
        Board.objects.create(title='Board 1', owner=self.user)
        Board.objects.create(title='Board 2', owner=self.other_user)

        response = self.client.get('/api/boards/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_get_board_detail_as_owner(self):
        """Test: Owner kann Board Details abrufen"""
        board = Board.objects.create(title='Board 1', owner=self.user)

        response = self.client.get(f'/api/boards/{board.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Board 1'

    def test_get_board_detail_no_access(self):
        """Test: Kein Zugriff auf fremdes Board"""
        board = Board.objects.create(title='Board 1', owner=self.other_user)

        response = self.client.get(f'/api/boards/{board.id}/')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_board_not_found(self):
        """Test: 404 wenn Board nicht existiert"""
        response = self.client.get('/api/boards/999/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_board_success(self):
        """Test: Owner kann Board Titel aktualisieren"""
        board = Board.objects.create(title='Alt', owner=self.user)
        data = {'title': 'Neu'}

        response = self.client.patch(f'/api/boards/{board.id}/', data, format='json')

        assert response.status_code == status.HTTP_200_OK
        board.refresh_from_db()
        assert board.title == 'Neu'

    def test_update_board_add_members(self):
        """Test: Owner kann Members hinzufügen"""
        board = Board.objects.create(title='Board', owner=self.user)
        data = {'members': [self.other_user.id]}

        response = self.client.patch(f'/api/boards/{board.id}/', data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert self.other_user in board.members.all()

    def test_delete_board_as_owner(self):
        """Test: Owner kann Board erfolgreich löschen"""
        board = Board.objects.create(title='Board', owner=self.user)

        response = self.client.delete(f'/api/boards/{board.id}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Board.objects.filter(id=board.id).exists()

    def test_delete_board_not_owner(self):
        """Test: Nicht-Owner kann Board nicht löschen"""
        board = Board.objects.create(title='Board', owner=self.other_user)
        board.members.add(self.user)

        response = self.client.delete(f'/api/boards/{board.id}/')

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Board.objects.filter(id=board.id).exists()

    def test_delete_board_not_found(self):
        """Test: 404 wenn Board nicht existiert"""
        response = self.client.delete('/api/boards/999/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_board_unauthenticated(self):
        """Test: Board löschen schlägt fehl ohne Authentication"""
        board = Board.objects.create(title='Board', owner=self.user)
        self.client.force_authenticate(user=None)

        response = self.client.delete(f'/api/boards/{board.id}/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestTasks:
    """Tests für Task CRUD Operationen"""

    def setup_method(self):
        """Erstellt Test User, Board und authentifizierten Client"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='owner@example.com',
            email='owner@example.com',
            password='password123'
        )
        self.other_user = User.objects.create_user(
            username='other@example.com',
            email='other@example.com',
            password='password123'
        )
        self.board = Board.objects.create(title='Board', owner=self.user)
        self.client.force_authenticate(user=self.user)

    def test_create_task_success(self):
        """Test: Task wird erfolgreich erstellt"""
        data = {
            'board': self.board.id,
            'title': 'Neue Task',
            'status': 'to-do',
            'priority': 'high'
        }
        response = self.client.post('/api/tasks/', data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'Neue Task'

    def test_create_task_not_board_member(self):
        """Test: Task erstellen schlägt fehl wenn User kein Board Member"""
        self.client.force_authenticate(user=self.other_user)
        data = {
            'board': self.board.id,
            'title': 'Neue Task'
        }
        response = self.client.post('/api/tasks/', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_tasks(self):
        """Test: User sieht Tasks von eigenen Boards"""
        Task.objects.create(
            board=self.board,
            title='Task 1',
            creator=self.user
        )

        response = self.client.get('/api/tasks/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_get_task_detail(self):
        """Test: Task Detail wird korrekt abgerufen"""
        task = Task.objects.create(
            board=self.board,
            title='Task 1',
            creator=self.user
        )

        response = self.client.get(f'/api/tasks/{task.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Task 1'

    def test_get_task_no_access(self):
        """Test: Kein Zugriff auf Task von fremdem Board"""
        other_board = Board.objects.create(title='Other', owner=self.other_user)
        task = Task.objects.create(
            board=other_board,
            title='Task 1',
            creator=self.other_user
        )

        response = self.client.get(f'/api/tasks/{task.id}/')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_task_success(self):
        """Test: Task wird erfolgreich aktualisiert"""
        task = Task.objects.create(
            board=self.board,
            title='Alt',
            creator=self.user
        )
        data = {'status': 'done'}

        response = self.client.patch(f'/api/tasks/{task.id}/', data, format='json')

        assert response.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.status == 'done'

    def test_delete_task_as_creator(self):
        """Test: Creator kann eigene Task löschen"""
        task = Task.objects.create(
            board=self.board,
            title='Task',
            creator=self.user
        )

        response = self.client.delete(f'/api/tasks/{task.id}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Task.objects.filter(id=task.id).exists()

    def test_delete_task_no_permission(self):
        """Test: Nicht-Creator kann Task nicht löschen"""
        self.board.members.add(self.other_user)
        task = Task.objects.create(
            board=self.board,
            title='Task',
            creator=self.user
        )

        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(f'/api/tasks/{task.id}/')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_tasks_by_reviewer(self):
        """Test: User sieht Tasks wo er Reviewer ist"""
        Task.objects.create(
            board=self.board,
            title='Task 1',
            creator=self.user,
            reviewer=self.user
        )

        response = self.client.get('/api/tasks/reviewing/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_get_tasks_by_reviewer_unauthenticated(self):
        """Test: Reviewing Endpoint schlägt fehl ohne Authentication"""
        self.client.force_authenticate(user=None)

        response = self.client.get('/api/tasks/reviewing/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_tasks_assigned_to_me(self):
        """Test: User sieht Tasks wo er Assignee ist"""
        Task.objects.create(
            board=self.board,
            title='Task 1',
            creator=self.user,
            assignee=self.user
        )

        response = self.client.get('/api/tasks/assigned-to-me/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_get_tasks_assigned_to_me_unauthenticated(self):
        """Test: Assigned-to-me schlägt fehl ohne Authentication"""
        self.client.force_authenticate(user=None)

        response = self.client.get('/api/tasks/assigned-to-me/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestComments:
    """Tests für Comment CRUD Operationen"""

    def setup_method(self):
        """Erstellt Test User, Board, Task und authentifizierten Client"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='owner@example.com',
            email='owner@example.com',
            password='password123'
        )
        self.other_user = User.objects.create_user(
            username='other@example.com',
            email='other@example.com',
            password='password123'
        )
        self.board = Board.objects.create(title='Board', owner=self.user)
        self.task = Task.objects.create(
            board=self.board,
            title='Task',
            creator=self.user
        )
        self.client.force_authenticate(user=self.user)

    def test_create_comment_success(self):
        """Test: Comment wird erfolgreich erstellt"""
        data = {'content': 'Mein Kommentar'}
        response = self.client.post(
            f'/api/tasks/{self.task.id}/comments/', data, format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['content'] == 'Mein Kommentar'

    def test_create_comment_empty_content(self):
        """Test: Comment erstellen schlägt fehl bei leerem Content"""
        data = {'content': ''}
        response = self.client.post(
            f'/api/tasks/{self.task.id}/comments/', data, format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_comments(self):
        """Test: Comments werden korrekt aufgelistet"""
        Comment.objects.create(
            task=self.task,
            content='Kommentar 1',
            author=self.user
        )

        response = self.client.get(f'/api/tasks/{self.task.id}/comments/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_delete_comment_as_author(self):
        """Test: Author kann eigenen Comment löschen"""
        comment = Comment.objects.create(
            task=self.task,
            content='Kommentar',
            author=self.user
        )

        response = self.client.delete(
            f'/api/tasks/{self.task.id}/comments/{comment.id}/'
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Comment.objects.filter(id=comment.id).exists()

    def test_delete_comment_no_permission(self):
        """Test: Nicht-Author kann Comment nicht löschen"""
        self.board.members.add(self.other_user)
        comment = Comment.objects.create(
            task=self.task,
            content='Kommentar',
            author=self.user
        )

        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(
            f'/api/tasks/{self.task.id}/comments/{comment.id}/'
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestEmailCheck:
    """Tests für Email-Check Endpoint"""

    def setup_method(self):
        """Erstellt Test User mit Profile und authentifizierten Client"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='owner@example.com',
            email='owner@example.com',
            password='password123'
        )
        UserProfile.objects.create(user=self.user, fullname='Owner Name')
        self.client.force_authenticate(user=self.user)

    def test_email_check_success(self):
        """Test: Email-Check findet existierenden User"""
        response = self.client.get('/api/email-check/', {'email': 'owner@example.com'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'owner@example.com'
        assert response.data['fullname'] == 'Owner Name'

    def test_email_check_missing_param(self):
        """Test: 400 wenn email Parameter fehlt"""
        response = self.client.get('/api/email-check/')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_email_check_invalid_format(self):
        """Test: 400 bei ungültigem Email-Format"""
        response = self.client.get('/api/email-check/', {'email': 'not-an-email'})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_email_check_not_found(self):
        """Test: 404 wenn Email nicht existiert"""
        response = self.client.get('/api/email-check/', {'email': 'unknown@example.com'})

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_email_check_unauthenticated(self):
        """Test: Email-Check schlägt fehl ohne Authentication"""
        self.client.force_authenticate(user=None)

        response = self.client.get('/api/email-check/', {'email': 'owner@example.com'})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
