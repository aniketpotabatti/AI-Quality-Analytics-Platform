"""Model registry ORM models."""

from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from has_api.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from has_api.infrastructure.database.types import GUID, JSONVariant


class ModelConfigModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "model_configs"

    workspace_id: Mapped[UUID] = mapped_column(
        GUID,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    config: Mapped[dict[str, object]] = mapped_column(JSONVariant, default=dict)
