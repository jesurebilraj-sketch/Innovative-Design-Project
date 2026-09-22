"""Test Supabase JWT authentication and operator role authorization."""

import time
import pytest
from app.core.auth import decode_and_verify_supabase_jwt
from app.core.exceptions import AuthenticationError, UnauthorizedOperatorError
from tests.conftest import create_mock_jwt


def test_valid_jwt_decoding():
    """Verify standard valid JWT token decodes correctly."""
    payload = {"sub": "user-123", "role": "operator", "exp": int(time.time()) + 3600}
    token = create_mock_jwt(payload)
    decoded = decode_and_verify_supabase_jwt(token, secret="skyops-jwt-secret-key-for-development")
    assert decoded["sub"] == "user-123"
    assert decoded["role"] == "operator"


def test_expired_jwt_rejected():
    """Verify expired token raises AuthenticationError."""
    payload = {"sub": "user-123", "role": "operator", "exp": int(time.time()) - 100}
    token = create_mock_jwt(payload)
    with pytest.raises(AuthenticationError) as exc_info:
        decode_and_verify_supabase_jwt(token, secret="skyops-jwt-secret-key-for-development")
    assert "expired" in str(exc_info.value)


def test_invalid_signature_rejected():
    """Verify token signed with wrong secret raises AuthenticationError."""
    payload = {"sub": "user-123", "role": "operator", "exp": int(time.time()) + 3600}
    token = create_mock_jwt(payload, secret="wrong-secret-key")
    with pytest.raises(AuthenticationError) as exc_info:
        decode_and_verify_supabase_jwt(token, secret="skyops-jwt-secret-key-for-development")
    assert "signature" in str(exc_info.value)
