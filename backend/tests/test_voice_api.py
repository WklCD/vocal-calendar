import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_user
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
    def test_ai_parse_placeholder(self, client, mock_user):
        def override_get_user():
            return mock_user
        app.dependency_overrides[get_current_user] = override_get_user

        response = client.post("/api/ai/parse?text=hello")
        assert response.status_code == 200

    def test_ai_detect_conflicts_placeholder(self, client, mock_user):
        def override_get_user():
            return mock_user
        app.dependency_overrides[get_current_user] = override_get_user

        response = client.post("/api/ai/detect-conflicts")
        assert response.status_code == 200

    def test_ai_daily_briefing_placeholder(self, client, mock_user):
        def override_get_user():
            return mock_user
        app.dependency_overrides[get_current_user] = override_get_user

        response = client.get("/api/ai/daily-briefing")
        assert response.status_code == 200
