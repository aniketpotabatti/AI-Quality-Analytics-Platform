"""Shared API response schemas and cross-cutting DTOs."""

from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class APIModel(BaseModel):
    """Base model for all API DTOs — forbid unknown fields, enable ORM mode."""

    model_config = ConfigDict(from_attributes=True, extra="forbid", populate_by_name=True)


class HealthResponse(APIModel):
    status: str = "ok"
    service: str = "has-api"
    version: str


class ReadyResponse(APIModel):
    status: str
    database: str
    redis: str


class ProblemDetail(APIModel):
    """RFC 7807 Problem Details for HTTP APIs."""

    type: str = "about:blank"
    title: str
    status: int
    detail: str
    code: str = Field(description="Application-specific error code")
    instance: str | None = Field(
        default=None,
        description="URI reference that identifies the specific occurrence",
    )


class PaginationMeta(APIModel):
    total: int = Field(ge=0, description="Total items matching the query")
    limit: int = Field(ge=1, le=200, description="Page size")
    offset: int = Field(ge=0, description="Number of items skipped")


class Page(APIModel, Generic[T]):
    """Generic paginated response envelope."""

    items: list[T]
    pagination: PaginationMeta


class MessageResponse(APIModel):
    message: str


class TimestampedMixin(APIModel):
    created_at: datetime
    updated_at: datetime


class WorkspaceScopedMixin(APIModel):
    workspace_id: UUID
