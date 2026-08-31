"""Workspace and membership DTOs."""

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from has_api.api.schemas.common import APIModel, TimestampedMixin
from has_api.api.schemas.enums import WorkspaceRole


class WorkspaceCreate(APIModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(
        min_length=2,
        max_length=100,
        description="URL-safe unique identifier (lowercase, hyphens allowed)",
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )


class WorkspaceUpdate(APIModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)


class WorkspaceResponse(TimestampedMixin):
    id: UUID
    name: str
    slug: str


class WorkspaceMemberResponse(APIModel):
    id: UUID
    workspace_id: UUID
    user_id: UUID
    email: EmailStr | None = None
    full_name: str | None = None
    role: WorkspaceRole
    created_at: datetime


class WorkspaceMemberCreate(APIModel):
    email: EmailStr
    role: WorkspaceRole = WorkspaceRole.MEMBER

    @field_validator("role")
    @classmethod
    def no_owner_via_invite(cls, value: WorkspaceRole) -> WorkspaceRole:
        if value == WorkspaceRole.OWNER:
            msg = "Cannot assign owner role via invite; transfer ownership separately"
            raise ValueError(msg)
        return value


class WorkspaceMemberUpdate(APIModel):
    role: WorkspaceRole

    @field_validator("role")
    @classmethod
    def no_owner_via_update(cls, value: WorkspaceRole) -> WorkspaceRole:
        if value == WorkspaceRole.OWNER:
            msg = "Cannot assign owner role via role update"
            raise ValueError(msg)
        return value
