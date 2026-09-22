"""Authentication and authorization dependencies for SkyOps backend."""

import base64
import hashlib
import hmac
import json
import time
from typing import Any, Dict, Optional
from fastapi import Depends, Header
from app.core.exceptions import AuthenticationError, UnauthorizedOperatorError
from app.core.settings import settings


def _urlsafe_b64decode(s: str) -> bytes:
    """Decode urlsafe base64 string, adding padding if needed."""
    remainder = len(s) % 4
    if remainder > 0:
        s += "=" * (4 - remainder)
    return base64.urlsafe_b64decode(s)


def decode_and_verify_supabase_jwt(token: str, secret: str) -> Dict[str, Any]:
    """Decode and verify Supabase JWT token using HS256.
    
    If secret is empty or verification is disabled in dev mode, decodes payload.
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise AuthenticationError("Malformed JWT format")

    header_raw, payload_raw, signature_raw = parts
    try:
        header = json.loads(_urlsafe_b64decode(header_raw).decode("utf-8"))
        payload = json.loads(_urlsafe_b64decode(payload_raw).decode("utf-8"))
    except Exception as e:
        raise AuthenticationError("Failed to decode token payload") from e

    # Check expiration if present
    exp = payload.get("exp")
    if exp is not None and time.time() > exp:
        raise AuthenticationError("Token has expired")

    # Verify signature if secret provided
    if secret:
        signing_input = f"{header_raw}.{payload_raw}".encode("utf-8")
        expected_sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
        actual_sig = _urlsafe_b64decode(signature_raw)
        if not hmac.compare_digest(expected_sig, actual_sig):
            raise AuthenticationError("Invalid token signature")

    return payload


def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """FastAPI dependency to extract and validate the authenticated user from Authorization header."""
    if not authorization:
        raise AuthenticationError("Missing Authorization header")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError("Invalid authorization format. Expected 'Bearer <token>'")

    token = parts[1]
    return decode_and_verify_supabase_jwt(token, settings.SUPABASE_JWT_SECRET)


def require_operator(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """FastAPI dependency requiring the 'operator' role in user metadata or app metadata."""
    # Supabase typically stores roles in app_metadata.roles or user_metadata.role or role claim
    role = user.get("role")
    app_metadata = user.get("app_metadata", {})
    user_metadata = user.get("user_metadata", {})

    roles = []
    if isinstance(role, str):
        roles.append(role)
    if "roles" in app_metadata and isinstance(app_metadata["roles"], list):
        roles.extend(app_metadata["roles"])
    if "role" in user_metadata:
        roles.append(user_metadata["role"])

    if "operator" not in roles and "admin" not in roles and "service_role" not in roles:
        raise UnauthorizedOperatorError("User lacks the required 'operator' role")

    return user
