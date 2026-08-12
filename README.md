# KanMind Backend

A Django REST Framework backend for KanMind, a Kanban board application. This backend provides a complete API for user authentication, board management, task tracking, and comments.

## Features

- User registration and token-based authentication
- Board creation and management with member handling
- Task management with status, priority, assignee, and reviewer
- Comment system for tasks
- Role-based permissions (owner, member, creator)

## Tech Stack

- Python 3.14
- Django 6.1
- Django REST Framework
- Token Authentication
- SQLite (development database)
- pytest & pytest-django (testing)

## Project Structure

Backend/
├── core/ # Main project settings, URLs
├── auth_app/ # Authentication (registration, login)
│ └── api/ # Serializers, views, urls, permissions
├── kanban_app/ # Boards, Tasks, Comments
│ └── api/ # Serializers, views, urls, permissions
├── manage.py
└── requirements.txt

## Getting Started

### Prerequisites

- Python 3.14 installed on your machine

### Installation

1. Clone the repository
```bash
git clone https://github.com/lvfranek/kanmind-backend
cd Backend
```

2. Create and activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Apply database migrations
```bash
python3 manage.py migrate
```

5. Create a superuser (to access the Django admin panel)
```bash
python3 manage.py createsuperuser
```

6. Start the development server
```bash
python3 manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/api/`
The admin panel will be available at `http://127.0.0.1:8000/admin/`

## Running Tests

This project uses pytest for testing. To run all tests with coverage report:

```bash
pytest --cov=auth_app --cov=kanban_app --cov-report=term
```

Current test coverage: 95%+

## API Endpoints

### Authentication
- `POST /api/registration/` - Register a new user
- `POST /api/login/` - Login and receive auth token

### Boards
- `GET /api/boards/` - List all boards for the authenticated user
- `POST /api/boards/` - Create a new board
- `GET /api/boards/{board_id}/` - Retrieve a specific board with its tasks
- `PATCH /api/boards/{board_id}/` - Update a board's title or members

### Tasks
- `GET /api/tasks/` - List all tasks for the authenticated user
- `POST /api/tasks/` - Create a new task
- `GET /api/tasks/{task_id}/` - Retrieve a specific task
- `PATCH /api/tasks/{task_id}/` - Update a task
- `DELETE /api/tasks/{task_id}/` - Delete a task
- `GET /api/tasks/reviewer/` - List tasks where the user is the reviewer

### Comments
- `GET /api/tasks/{task_id}/comments/` - List all comments for a task
- `POST /api/tasks/{task_id}/comments/` - Add a comment to a task
- `DELETE /api/tasks/{task_id}/comments/{comment_id}/` - Delete a comment

## Authentication

All endpoints (except registration and login) require a token in the request header:

Authorization: Token <your-token-here>

The token is returned upon successful registration or login.

## Notes

- The database file (`db.sqlite3`) is not included in this repository, as per project requirements. It will be created automatically after running migrations.
- This backend is designed to work with the KanMind frontend, tested via Postman during development.

## Frontend

This backend is designed to work together with the KanMind frontend, available here:
https://github.com/Developer-Akademie-Backendkurs/project.KanMind

### Running Backend and Frontend together

1. Make sure the backend is running (see "Getting Started" above) at `http://127.0.0.1:8000/`

2. Clone the frontend repository in a separate folder
```bash
git clone https://github.com/Developer-Akademie-Backendkurs/project.KanMind frontend
```

3. Open the frontend project and locate the file where the API base URL is configured (check the project's own documentation for the exact file name and variable).

4. Set the API base URL to point to this backend:
http://127.0.0.1:8000/api

5. Open the frontend (e.g. via a local server or by opening the HTML file, depending on the frontend setup) and it will communicate with this backend.

**Note:** During development, this backend was tested primarily using Postman rather than the frontend, to verify API behavior independently.