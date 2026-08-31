"""JWT token creation and verification using python-jose."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from jose import JWTError, jwt
from pydantic import BaseModel

from has_api.config import get_settings


class TokenPayload(BaseModel):
    sub: str  # user_id as string
    workspace_id: str | None = None
    type: str  # "access" | "refresh"
    exp: datetime
    iat: datetime


def _settings():
    return get_settings()


def create_access_token(user_id: UUID, workspace_id: UUID | None = None) -> str:
    """Encode a short-lived access JWT."""
    settings = _settings()
    now = datetime.now(UTC)
    expires = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "workspace_id": str(workspace_id) if workspace_id else None,
        "type": "access",
        "iat": now,
        "exp": expires,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


def create_refresh_token(user_id: UUID) -> str:
    """Encode a long-lived refresh JWT."""
    settings = _settings()
    now = datetime.now(UTC)
    expires = now + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload = {
        "sub": str(user_id),
        "workspace_id": None,
        "type": "refresh",
        "iat": now,
        "exp": expires,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


def decode_token(token: str) -> TokenPayload | None:
    """Decode and validate a JWT. Returns None on any error."""
    try:
        settings = _settings()
        raw = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        return TokenPayload(**raw)
    except (JWTError, Exception):
        return None
