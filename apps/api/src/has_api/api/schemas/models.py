"""Model registry DTOs."""

from typing import Any
from uuid import UUID

from pydantic import Field

from has_api.api.schemas.common import APIModel, TimestampedMixin, WorkspaceScopedMixin
from has_api.api.schemas.enums import LlmProvider


class ModelConfigCreate(APIModel):
    name: str = Field(min_length=1, max_length=255)
    provider: LlmProvider
    model_id: str = Field(min_length=1, max_length=255, description="Provider model identifier")
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific options (temperature, max_tokens, etc.)",
    )


class ModelConfigUpdate(APIModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    provider: LlmProvider | None = None
    model_id: str | None = Field(default=None, min_length=1, max_length=255)
    config: dict[str, Any] | None = None


class ModelConfigResponse(WorkspaceScopedMixin, TimestampedMixin):
    id: UUID
    name: str
    provider: LlmProvider
    model_id: str
    config: dict[str, Any] = Field(default_factory=dict)
