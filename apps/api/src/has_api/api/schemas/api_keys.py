"""API key DTOs."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from has_api.api.schemas.common import APIModel, WorkspaceScopedMixin


class ApiKeyCreate(APIModel):
    name: str = Field(min_length=1, max_length=255)
    expires_at: datetime | None = Field(
        default=None,
        description="Optional expiry; null means no expiry",
    )


class ApiKeyResponse(WorkspaceScopedMixin):
    """Public representation — never includes the raw secret."""

    id: UUID
    name: str
    key_prefix: str = Field(description="First characters of the key for identification")
    is_active: bool
    last_used_at: datetime | None = None
    expires_at: datetime | None = None
    created_by_id: UUID | None = None
    created_at: datetime


class ApiKeyCreatedResponse(ApiKeyResponse):
    """Returned once on creation; includes the raw secret."""

    raw_key: str = Field(
        description="Full API key secret — shown only once; store securely",
    )
