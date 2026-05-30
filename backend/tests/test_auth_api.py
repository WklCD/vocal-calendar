import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db, Base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

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


class TestRegisterAPI:
    def test_register_success(self, client):
        response = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["email"] == "test@example.com"

    def test_register_duplicate_email(self, client):
        client.post("/api/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
        })
        response = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "username": "another",
            "password": "password123",
        })
        assert response.status_code == 400


class TestLoginAPI:
    def test_login_success(self, client):
        client.post("/api/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
        })
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "password123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]

    def test_login_wrong_password(self, client):
        client.post("/api/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
        })
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword",
        })
        assert response.status_code == 401


class TestMeAPI:
    def test_get_me(self, client):
        client.post("/api/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
        })
        login_resp = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "password123",
        })
        token = login_resp.json()["data"]["access_token"]

        response = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {token}",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["email"] == "test@example.com"

    def test_get_me_no_token(self, client):
        response = client.get("/api/auth/me")
        assert response.status_code == 401
