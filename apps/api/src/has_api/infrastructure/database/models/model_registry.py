"""Model registry ORM models."""

from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from has_api.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ModelConfigModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "model_configs"

    workspace_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    config: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
