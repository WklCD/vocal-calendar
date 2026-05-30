import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_user
from app.api.ai import get_ai_service
from app.models.user import User


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_user():
    user = MagicMock(spec=User)
    user.id = "test-user-id"
    user.email = "test@example.com"
    user.username = "testuser"
    return user


@pytest.fixture(autouse=True)
def cleanup_overrides():
    yield
    app.dependency_overrides.clear()


class TestVoiceAPI:
    def test_voice_help_endpoint(self, client, mock_user):
        def override_get_user():
            return mock_user
        app.dependency_overrides[get_current_user] = override_get_user

        response = client.get("/api/voice/help")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert len(data["data"]) > 0
        assert "command" in data["data"][0]

    @pytest.mark.skip(reason="Requires voice_logs table migration")
    def test_voice_logs_endpoint(self, client, mock_user):
        def override_get_user():
            return mock_user
        app.dependency_overrides[get_current_user] = override_get_user

        response = client.get("/api/voice/logs")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0


class TestAIEndpoints:
    def test_ai_detect_conflicts(self, client, mock_user):
        def override_get_user():
            return mock_user

        mock_service = MagicMock()
        mock_service.detect_conflicts.return_value = []
        app.dependency_overrides[get_current_user] = override_get_user
        app.dependency_overrides[get_ai_service] = lambda: mock_service

        response = client.post(
            "/api/ai/detect-conflicts",
            params={"start_time": "2026-06-01T10:00:00Z", "end_time": "2026-06-01T11:00:00Z"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["conflicts"] == []

    def test_ai_recommend_slot(self, client, mock_user):
        def override_get_user():
            return mock_user

        mock_service = MagicMock()
        mock_service.recommend_free_slots.return_value = [
            {"start": "2026-06-01T09:00:00+00:00", "end": "2026-06-01T18:00:00+00:00", "duration_minutes": 540},
        ]
        app.dependency_overrides[get_current_user] = override_get_user
        app.dependency_overrides[get_ai_service] = lambda: mock_service

        response = client.post(
            "/api/ai/recommend-slot",
            params={"target_date": "2026-06-01", "duration_minutes": 60},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert len(data["data"]["slots"]) == 1

    def test_ai_daily_briefing(self, client, mock_user):
        def override_get_user():
            return mock_user

        mock_service = MagicMock()
        mock_service.generate_daily_briefing = AsyncMock(return_value="今天没有安排。")
        app.dependency_overrides[get_current_user] = override_get_user
        app.dependency_overrides[get_ai_service] = lambda: mock_service

        response = client.get("/api/ai/daily-briefing")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "briefing" in data["data"]
