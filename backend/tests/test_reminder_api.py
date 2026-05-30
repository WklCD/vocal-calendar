import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.reminder import Reminder


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_user():
    user = MagicMock(spec=User)
    user.id = "user-1"
    user.email = "test@example.com"
    user.username = "testuser"
    return user


@pytest.fixture
def mock_db():
    return MagicMock()


class TestListReminders:
    def test_list_reminders_success(self, client, mock_user, mock_db):
        mock_reminder = MagicMock()
        mock_reminder.id = "reminder-1"
        mock_reminder.event_id = "event-1"
        mock_reminder.user_id = "user-1"
        mock_reminder.remind_at = datetime.now(timezone.utc)
        mock_reminder.type = "push"
        mock_reminder.status = "pending"
        mock_reminder.created_at = datetime.now(timezone.utc)

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [mock_reminder]
        mock_db.query.return_value = mock_query

        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db

        response = client.get("/api/reminders", headers={"Authorization": "Bearer test-token"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

        app.dependency_overrides.clear()

    def test_list_reminders_with_status_filter(self, client, mock_user, mock_db):
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db

        response = client.get("/api/reminders?status=pending", headers={"Authorization": "Bearer test-token"})
        assert response.status_code == 200

        app.dependency_overrides.clear()

    def test_list_reminders_no_token(self, client):
        response = client.get("/api/reminders")
        assert response.status_code == 401


class TestDismissReminder:
    def test_dismiss_reminder_success(self, client, mock_user, mock_db):
        mock_reminder = MagicMock()
        mock_reminder.id = "reminder-1"
        mock_reminder.event_id = "event-1"
        mock_reminder.user_id = "user-1"
        mock_reminder.remind_at = datetime.now(timezone.utc)
        mock_reminder.type = "push"
        mock_reminder.status = "dismissed"
        mock_reminder.created_at = datetime.now(timezone.utc)

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_reminder
        mock_db.query.return_value = mock_query
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db

        response = client.put("/api/reminders/reminder-1/dismiss", headers={"Authorization": "Bearer test-token"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "dismissed"

        app.dependency_overrides.clear()

    def test_dismiss_reminder_not_found(self, client, mock_user, mock_db):
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db

        response = client.put("/api/reminders/nonexistent/dismiss", headers={"Authorization": "Bearer test-token"})
        assert response.status_code == 404

        app.dependency_overrides.clear()

    def test_dismiss_reminder_no_token(self, client):
        response = client.put("/api/reminders/reminder-1/dismiss")
        assert response.status_code == 401
