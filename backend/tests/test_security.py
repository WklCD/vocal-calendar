import pytest
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


class TestPasswordHashing:
    def test_hash_password_returns_string(self):
        result = hash_password("mypassword123")
        assert isinstance(result, str)
        assert result != "mypassword123"

    def test_verify_password_correct(self):
        hashed = hash_password("mypassword123")
        assert verify_password("mypassword123", hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("mypassword123")
        assert verify_password("wrongpassword", hashed) is False


class TestJWTToken:
    def test_create_access_token(self):
        token = create_access_token({"sub": "user-123"})
        assert isinstance(token, str)
        assert len(token) > 20

    def test_create_refresh_token(self):
        token = create_refresh_token({"sub": "user-123"})
        assert isinstance(token, str)
        assert len(token) > 20

    def test_decode_access_token(self):
        token = create_access_token({"sub": "user-123"})
        payload = decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"

    def test_decode_refresh_token(self):
        token = create_refresh_token({"sub": "user-123"})
        payload = decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["type"] == "refresh"

    def test_decode_invalid_token(self):
        payload = decode_token("invalid.token.here")
        assert payload is None
