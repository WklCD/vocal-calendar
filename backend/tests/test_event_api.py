import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "postgresql://vocal_user:vocal_pass@localhost:5432/vocal_calendar_test"
test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    client.post("/api/auth/register", json={"email": "test@example.com", "username": "testuser", "password": "password123"})
    resp = client.post("/api/auth/login", json={"email": "test@example.com", "password": "password123"})
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestEventCRUD:
    def test_create_event(self, client, auth_headers):
        response = client.post("/api/events", json={"title": "测试会议", "start_time": "2026-06-01T10:00:00Z", "end_time": "2026-06-01T11:00:00Z"}, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["title"] == "测试会议"

    def test_get_events(self, client, auth_headers):
        client.post("/api/events", json={"title": "会议A", "start_time": "2026-06-01T10:00:00Z", "end_time": "2026-06-01T11:00:00Z"}, headers=auth_headers)
        response = client.get("/api/events?start=2026-06-01T00:00:00Z&end=2026-06-02T00:00:00Z", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()["data"]) == 1

    def test_update_event(self, client, auth_headers):
        create_resp = client.post("/api/events", json={"title": "旧标题", "start_time": "2026-06-01T10:00:00Z", "end_time": "2026-06-01T11:00:00Z"}, headers=auth_headers)
        event_id = create_resp.json()["data"]["id"]
        response = client.put(f"/api/events/{event_id}", json={"title": "新标题"}, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["title"] == "新标题"

    def test_delete_event(self, client, auth_headers):
        create_resp = client.post("/api/events", json={"title": "要删除的事件", "start_time": "2026-06-01T10:00:00Z", "end_time": "2026-06-01T11:00:00Z"}, headers=auth_headers)
        event_id = create_resp.json()["data"]["id"]
        response = client.delete(f"/api/events/{event_id}", headers=auth_headers)
        assert response.status_code == 200

    def test_search_events(self, client, auth_headers):
        client.post("/api/events", json={"title": "项目评审会议", "start_time": "2026-06-01T10:00:00Z", "end_time": "2026-06-01T11:00:00Z"}, headers=auth_headers)
        response = client.get("/api/events/search?q=评审", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()["data"]) == 1
