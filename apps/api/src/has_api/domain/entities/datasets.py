"""Datasets bounded context entities."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(kw_only=True)
class Dataset:
    id: UUID = field(default_factory=uuid4)
    workspace_id: UUID
    name: str
    description: str | None = None
    created_by_id: UUID
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(kw_only=True)
class TestCase:
    id: UUID = field(default_factory=uuid4)
    dataset_id: UUID
    prompt: str
    response: str
    context: str | None = None
    ground_truth: str | None = None
    external_id: str | None = None
    sort_order: int = 0
    metadata: dict[str, object] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
