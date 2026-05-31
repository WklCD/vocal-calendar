import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from app.services.auth_service import AuthService
from app.models.user import User


@pytest.fixture
def db():
    return MagicMock(spec=Session)


@pytest.fixture
def service(db):
    return AuthService(db)


class TestRegister:
    def test_register_new_user(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        result = service.register("test@example.com", "testuser", "password123")

        assert db.add.called
        assert db.commit.called

    def test_register_duplicate_email(self, service, db):
        existing = User(email="test@example.com", username="existing", password_hash="hash")
        db.query.return_value.filter.return_value.first.return_value = existing

        with pytest.raises(ValueError, match="邮箱已被注册"):
            service.register("test@example.com", "newuser", "password123")


class TestLogin:
    def test_login_success(self, service, db):
        from app.core.security import hash_password
        user = User(
            id="user-1",
            email="test@example.com",
            username="testuser",
            password_hash=hash_password("password123"),
        )
        db.query.return_value.filter.return_value.first.return_value = user

        result = service.login("test@example.com", "password123")

        assert "access_token" in result
        assert "refresh_token" in result

    def test_login_wrong_password(self, service, db):
        from app.core.security import hash_password
        user = User(
            id="user-1",
            email="test@example.com",
            username="testuser",
            password_hash=hash_password("password123"),
        )
        db.query.return_value.filter.return_value.first.return_value = user

        with pytest.raises(ValueError, match="邮箱或密码错误"):
            service.login("test@example.com", "wrongpassword")

    def test_login_nonexistent_user(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="邮箱或密码错误"):
            service.login("noone@example.com", "password123")
