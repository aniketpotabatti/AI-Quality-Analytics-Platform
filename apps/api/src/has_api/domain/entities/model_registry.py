"""Model registry bounded context entities."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from has_api.domain.value_objects import LlmProvider


@dataclass(kw_only=True)
class ModelConfig:
    id: UUID = field(default_factory=uuid4)
    workspace_id: UUID
    name: str
    provider: LlmProvider
    model_id: str
    config: dict[str, object] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
