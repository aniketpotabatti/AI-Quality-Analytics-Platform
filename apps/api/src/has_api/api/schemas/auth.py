"""Auth request/response DTOs."""

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from has_api.api.schemas.common import APIModel
from has_api.api.schemas.enums import WorkspaceRole


class RegisterRequest(APIModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    workspace_name: str = Field(
        min_length=1,
        max_length=255,
        description="Name of the initial workspace created for the user",
    )

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if value.isspace():
            msg = "Password cannot be blank"
            raise ValueError(msg)
        return value


class LoginRequest(APIModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(APIModel):
    refresh_token: str = Field(min_length=1)


class TokenResponse(APIModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token lifetime in seconds")


class UserResponse(APIModel):
    id: UUID
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime


class MeResponse(APIModel):
    user: UserResponse
    workspaces: list["WorkspaceMembershipSummary"]


class WorkspaceMembershipSummary(APIModel):
    workspace_id: UUID
    workspace_name: str
    workspace_slug: str
    role: WorkspaceRole


MeResponse.model_rebuild()
