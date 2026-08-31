"""Identity bounded context entities."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from has_api.domain.value_objects import WorkspaceRole


@dataclass(kw_only=True)
class Workspace:
    id: UUID = field(default_factory=uuid4)
    name: str
    slug: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(kw_only=True)
class User:
    id: UUID = field(default_factory=uuid4)
    email: str
    hashed_password: str
    full_name: str
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(kw_only=True)
class WorkspaceMember:
    id: UUID = field(default_factory=uuid4)
    workspace_id: UUID
    user_id: UUID
    role: WorkspaceRole = WorkspaceRole.MEMBER
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(kw_only=True)
class ApiKey:
    id: UUID = field(default_factory=uuid4)
    workspace_id: UUID
    name: str
    key_hash: str
    key_prefix: str
    created_by_id: UUID
    is_active: bool = True
    last_used_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
