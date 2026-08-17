import pytest
from django.contrib.auth.models import User

from rest_framework.test import APIClient
from rest_framework import status

from auth_app.models import UserProfile
from kanban_app.models import Board, Task, Comment


@pytest.mark.django_db
class TestBoards:
    """Tests for Board CRUD operations"""

    def setup_method(self):
        """Creates test user and authenticated client"""
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
        """Test: Board is created successfully"""
        data = {'title': 'My Board', 'members': []}
        response = self.client.post('/api/boards/', data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'My Board'
        assert response.data['owner_id'] == self.user.id

    def test_create_board_unauthenticated(self):
        """Test: Board create fails without authentication"""
        self.client.force_authenticate(user=None)
        data = {'title': 'My Board'}
        response = self.client.post('/api/boards/', data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_boards(self):
        """Test: User sees only their own boards"""
        Board.objects.create(title='Board 1', owner=self.user)
        Board.objects.create(title='Board 2', owner=self.other_user)

        response = self.client.get('/api/boards/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_get_board_detail_as_owner(self):
        """Test: Owner can retrieve board details"""
        board = Board.objects.create(title='Board 1', owner=self.user)
        board.members.add(self.other_user)

        response = self.client.get(f'/api/boards/{board.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Board 1'
        assert response.data['owner_id'] == self.user.id
        assert response.data['members'][0]['fullname'] == self.other_user.email
        assert 'tasks' in response.data
        assert 'members_data' not in response.data

    def test_get_board_detail_includes_tasks(self):
        """Test: Board detail includes nested tasks without a board field"""
        board = Board.objects.create(title='Board 1', owner=self.user)
        Task.objects.create(
            board=board, title='Task 1', creator=self.user,
            assignee=self.other_user, status='to-do', priority='high'
        )

        response = self.client.get(f'/api/boards/{board.id}/')

        task_data = response.data['tasks'][0]
        assert task_data['title'] == 'Task 1'
        assert task_data['assignee']['fullname'] == self.other_user.email
        assert task_data['comments_count'] == 0
        assert 'board' not in task_data

    def test_list_boards_task_counts(self):
        """Test: Board list shows correct task counts instead of placeholders"""
        board = Board.objects.create(title='Board 1', owner=self.user)
        Task.objects.create(
            board=board, title='Task 1', creator=self.user,
            status='to-do', priority='high'
        )
        Task.objects.create(
            board=board, title='Task 2', creator=self.user,
            status='done', priority='low'
        )

        response = self.client.get('/api/boards/')

        data = response.data[0]
        assert data['ticket_count'] == 2
        assert data['tasks_to_do_count'] == 1
        assert data['tasks_high_prio_count'] == 1

    def test_get_board_detail_no_access(self):
        """Test: No access to another user's board"""
        board = Board.objects.create(title='Board 1', owner=self.other_user)

        response = self.client.get(f'/api/boards/{board.id}/')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_board_not_found(self):
        """Test: 404 when the board does not exist"""
        response = self.client.get('/api/boards/999/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_board_success(self):
        """Test: Owner can update the board title"""
        board = Board.objects.create(title='Old', owner=self.user)
        data = {'title': 'New'}

        response = self.client.patch(f'/api/boards/{board.id}/', data, format='json')

        assert response.status_code == status.HTTP_200_OK
        board.refresh_from_db()
        assert board.title == 'New'

    def test_update_board_add_members(self):
        """Test: Owner can add members"""
        board = Board.objects.create(title='Board', owner=self.user)
        data = {'members': [self.other_user.id]}

        response = self.client.patch(f'/api/boards/{board.id}/', data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert self.other_user in board.members.all()

    def test_update_board_response_format(self):
        """Test: PATCH board returns owner_data/members_data, no tasks field"""
        board = Board.objects.create(title='Board', owner=self.user)
        data = {'members': [self.other_user.id]}

        response = self.client.patch(f'/api/boards/{board.id}/', data, format='json')

        assert response.data['owner_data']['id'] == self.user.id
        assert response.data['members_data'][0]['id'] == self.other_user.id
        assert 'tasks' not in response.data
        assert 'members' not in response.data

    def test_delete_board_as_owner(self):
        """Test: Owner can delete a board successfully"""
        board = Board.objects.create(title='Board', owner=self.user)

        response = self.client.delete(f'/api/boards/{board.id}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Board.objects.filter(id=board.id).exists()

    def test_delete_board_not_owner(self):
        """Test: Non-owner cannot delete a board"""
        board = Board.objects.create(title='Board', owner=self.other_user)
        board.members.add(self.user)

        response = self.client.delete(f'/api/boards/{board.id}/')

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Board.objects.filter(id=board.id).exists()

    def test_delete_board_not_found(self):
        """Test: 404 when the board does not exist"""
        response = self.client.delete('/api/boards/999/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_board_unauthenticated(self):
        """Test: Board delete fails without authentication"""
        board = Board.objects.create(title='Board', owner=self.user)
        self.client.force_authenticate(user=None)

        response = self.client.delete(f'/api/boards/{board.id}/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestTasks:
    """Tests for Task CRUD operations"""

    def setup_method(self):
        """Creates test user, board and authenticated client"""
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
        """Test: Task is created successfully"""
        data = {
            'board': self.board.id,
            'title': 'New Task',
            'status': 'to-do',
            'priority': 'high'
        }
        response = self.client.post('/api/tasks/', data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'New Task'

    def test_create_task_not_board_member(self):
        """Test: Task create returns 403 when the user is not a board member"""
        self.client.force_authenticate(user=self.other_user)
        data = {
            'board': self.board.id,
            'title': 'New Task'
        }
        response = self.client.post('/api/tasks/', data, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_task_board_not_found(self):
        """Test: Task create returns 404 when the board does not exist"""
        data = {
            'board': 999,
            'title': 'New Task'
        }
        response = self.client.post('/api/tasks/', data, format='json')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_tasks(self):
        """Test: User sees tasks from their own boards"""
        Task.objects.create(
            board=self.board,
            title='Task 1',
            creator=self.user
        )

        response = self.client.get('/api/tasks/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_get_task_detail(self):
        """Test: Task detail is retrieved correctly"""
        task = Task.objects.create(
            board=self.board,
            title='Task 1',
            creator=self.user
        )

        response = self.client.get(f'/api/tasks/{task.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Task 1'

    def test_get_task_no_access(self):
        """Test: No access to a task from another user's board"""
        other_board = Board.objects.create(title='Other', owner=self.other_user)
        task = Task.objects.create(
            board=other_board,
            title='Task 1',
            creator=self.other_user
        )

        response = self.client.get(f'/api/tasks/{task.id}/')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_task_success(self):
        """Test: Task is updated successfully"""
        task = Task.objects.create(
            board=self.board,
            title='Old',
            creator=self.user
        )
        data = {'status': 'done'}

        response = self.client.patch(f'/api/tasks/{task.id}/', data, format='json')

        assert response.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.status == 'done'

    def test_update_task_response_format(self):
        """Test: PATCH task response has no board and no comments_count"""
        task = Task.objects.create(
            board=self.board,
            title='Old',
            creator=self.user
        )
        data = {'status': 'done'}

        response = self.client.patch(f'/api/tasks/{task.id}/', data, format='json')

        assert 'board' not in response.data
        assert 'comments_count' not in response.data

    def test_task_assignee_fullname_fallback_without_profile(self):
        """Test: assignee without a profile uses email as fullname fallback"""
        task = Task.objects.create(
            board=self.board, title='Task', creator=self.user,
            assignee=self.other_user
        )

        response = self.client.get(f'/api/tasks/{task.id}/')

        assert response.data['assignee']['fullname'] == self.other_user.email

    def test_task_assignee_fullname_with_profile(self):
        """Test: assignee with a profile uses fullname from the profile"""
        UserProfile.objects.create(user=self.other_user, fullname='Other Name')
        task = Task.objects.create(
            board=self.board, title='Task', creator=self.user,
            assignee=self.other_user
        )

        response = self.client.get(f'/api/tasks/{task.id}/')

        assert response.data['assignee']['fullname'] == 'Other Name'

    def test_delete_task_as_creator(self):
        """Test: Creator can delete their own task"""
        task = Task.objects.create(
            board=self.board,
            title='Task',
            creator=self.user
        )

        response = self.client.delete(f'/api/tasks/{task.id}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Task.objects.filter(id=task.id).exists()

    def test_delete_task_no_permission(self):
        """Test: Non-creator cannot delete a task"""
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
        """Test: User sees tasks where they are Reviewer"""
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
        """Test: Reviewing endpoint fails without authentication"""
        self.client.force_authenticate(user=None)

        response = self.client.get('/api/tasks/reviewing/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_tasks_assigned_to_me(self):
        """Test: User sees tasks where they are Assignee"""
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
        """Test: Assigned-to-me fails without authentication"""
        self.client.force_authenticate(user=None)

        response = self.client.get('/api/tasks/assigned-to-me/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestComments:
    """Tests for Comment CRUD operations"""

    def setup_method(self):
        """Creates test user, board, task and authenticated client"""
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
        """Test: Comment is created successfully"""
        data = {'content': 'My comment'}
        response = self.client.post(
            f'/api/tasks/{self.task.id}/comments/', data, format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['content'] == 'My comment'

    def test_create_comment_author_fullname(self):
        """Test: Author is returned as fullname from the profile"""
        UserProfile.objects.create(user=self.user, fullname='Owner Name')
        data = {'content': 'My comment'}

        response = self.client.post(
            f'/api/tasks/{self.task.id}/comments/', data, format='json'
        )

        assert response.data['author'] == 'Owner Name'

    def test_create_comment_empty_content(self):
        """Test: Comment create fails with empty content"""
        data = {'content': ''}
        response = self.client.post(
            f'/api/tasks/{self.task.id}/comments/', data, format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_comments(self):
        """Test: Comments are listed correctly"""
        Comment.objects.create(
            task=self.task,
            content='Comment 1',
            author=self.user
        )

        response = self.client.get(f'/api/tasks/{self.task.id}/comments/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_delete_comment_as_author(self):
        """Test: Author can delete their own comment"""
        comment = Comment.objects.create(
            task=self.task,
            content='Comment',
            author=self.user
        )

        response = self.client.delete(
            f'/api/tasks/{self.task.id}/comments/{comment.id}/'
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Comment.objects.filter(id=comment.id).exists()

    def test_delete_comment_no_permission(self):
        """Test: Non-author cannot delete a comment"""
        self.board.members.add(self.other_user)
        comment = Comment.objects.create(
            task=self.task,
            content='Comment',
            author=self.user
        )

        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(
            f'/api/tasks/{self.task.id}/comments/{comment.id}/'
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestEmailCheck:
    """Tests for the Email-Check endpoint"""

    def setup_method(self):
        """Creates test user with profile and authenticated client"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='owner@example.com',
            email='owner@example.com',
            password='password123'
        )
        UserProfile.objects.create(user=self.user, fullname='Owner Name')
        self.client.force_authenticate(user=self.user)

    def test_email_check_success(self):
        """Test: Email-Check finds an existing user"""
        response = self.client.get('/api/email-check/', {'email': 'owner@example.com'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'owner@example.com'
        assert response.data['fullname'] == 'Owner Name'

    def test_email_check_missing_param(self):
        """Test: 400 when the email parameter is missing"""
        response = self.client.get('/api/email-check/')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_email_check_invalid_format(self):
        """Test: 400 with an invalid email format"""
        response = self.client.get('/api/email-check/', {'email': 'not-an-email'})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_email_check_not_found(self):
        """Test: 404 when the email does not exist"""
        response = self.client.get('/api/email-check/', {'email': 'unknown@example.com'})

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_email_check_unauthenticated(self):
        """Test: Email-Check fails without authentication"""
        self.client.force_authenticate(user=None)

        response = self.client.get('/api/email-check/', {'email': 'owner@example.com'})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
