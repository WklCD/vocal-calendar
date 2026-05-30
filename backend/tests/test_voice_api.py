import pytest
from unittest.mock import AsyncMock, MagicMock, patch
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

    def test_tts_requires_auth(self, client):
        """未认证请求应返回 401 或 403。"""
        response = client.post(
            "/api/ai/tts",
            json={"text": "你好"},
        )
        assert response.status_code in (401, 403)

    @patch("app.api.ai.get_settings")
    @patch("app.api.ai.httpx.AsyncClient")
    def test_tts_success(self, mock_client_cls, mock_get_settings, client, mock_user):
        """已认证请求应返回 base64 音频数据。"""
        def override_get_user():
            return mock_user
        app.dependency_overrides[get_current_user] = override_get_user

        mock_settings = MagicMock()
        mock_settings.MIMO_API_KEY = "test-key"
        mock_get_settings.return_value = mock_settings

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "choices": [
                {
                    "message": {
                        "audio": {"data": "UklGRiQAAABXQVZFZm10IBAAAAABAAEA"},
                    }
                }
            ]
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        response = client.post(
            "/api/ai/tts",
            json={"text": "你好世界", "voice": "mimo_default"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "audio" in data["data"]
        assert data["data"]["audio"] == "UklGRiQAAABXQVZFZm10IBAAAAABAAEA"

    @patch("app.api.ai.get_settings")
    def test_tts_missing_api_key(self, mock_get_settings, client, mock_user):
        """未配置 MIMO_API_KEY 时应返回 500。"""
        def override_get_user():
            return mock_user
        app.dependency_overrides[get_current_user] = override_get_user

        mock_settings = MagicMock()
        mock_settings.MIMO_API_KEY = ""
        mock_get_settings.return_value = mock_settings

        response = client.post(
            "/api/ai/tts",
            json={"text": "你好"},
        )
        assert response.status_code == 500
        assert "MIMO_API_KEY" in response.json()["detail"]
