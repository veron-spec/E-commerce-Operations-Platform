"""Unit tests for auth utilities — password hashing and JWT token management."""
from app.core.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password():
    hashed = hash_password("mypassword")
    assert hashed != "mypassword"
    assert hashed.startswith("$2b$")


def test_verify_password_correct():
    hashed = hash_password("correct_password")
    assert verify_password("correct_password", hashed)


def test_verify_password_incorrect():
    hashed = hash_password("correct_password")
    assert not verify_password("wrong_password", hashed)


def test_create_and_decode_token():
    token = create_access_token(user_id=1, email="test@example.com")
    assert isinstance(token, str)
    assert len(token) > 20

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "1"
    assert payload["email"] == "test@example.com"
    assert "exp" in payload


def test_decode_invalid_token():
    payload = decode_access_token("invalid.token.string")
    assert payload is None


def test_decode_expired_token():
    """Token with exp in the past should be rejected."""
    from datetime import datetime, timedelta, timezone
    from jose import jwt
    from app.config import settings

    payload = {
        "sub": "1",
        "email": "test@example.com",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    expired = jwt.encode(payload, settings.secret_key, algorithm="HS256")
    assert decode_access_token(expired) is None
