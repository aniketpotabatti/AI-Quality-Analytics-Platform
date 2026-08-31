"""Dataset and test-case DTOs."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from has_api.api.schemas.common import APIModel, TimestampedMixin, WorkspaceScopedMixin


class DatasetCreate(APIModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10_000)


class DatasetUpdate(APIModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10_000)


class DatasetResponse(WorkspaceScopedMixin, TimestampedMixin):
    id: UUID
    name: str
    description: str | None = None
    created_by_id: UUID | None = None
    test_case_count: int | None = Field(
        default=None,
        description="Present when list/detail includes a count aggregation",
    )


class TestCaseCreate(APIModel):
    prompt: str = Field(min_length=1)
    response: str = Field(min_length=1)
    context: str | None = None
    ground_truth: str | None = None
    external_id: str | None = Field(default=None, max_length=255)
    sort_order: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TestCaseUpdate(APIModel):
    prompt: str | None = Field(default=None, min_length=1)
    response: str | None = Field(default=None, min_length=1)
    context: str | None = None
    ground_truth: str | None = None
    external_id: str | None = Field(default=None, max_length=255)
    sort_order: int | None = Field(default=None, ge=0)
    metadata: dict[str, Any] | None = None


class TestCaseResponse(TimestampedMixin):
    id: UUID
    dataset_id: UUID
    prompt: str
    response: str
    context: str | None = None
    ground_truth: str | None = None
    external_id: str | None = None
    sort_order: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class TestCaseBulkCreate(APIModel):
    items: list[TestCaseCreate] = Field(min_length=1, max_length=1000)


class TestCaseBulkCreateResponse(APIModel):
    created: int
    items: list[TestCaseResponse]
