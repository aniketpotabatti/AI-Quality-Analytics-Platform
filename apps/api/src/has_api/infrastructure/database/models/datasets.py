"""Dataset ORM models."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from has_api.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from has_api.infrastructure.database.models.evaluations import EvaluationRunModel
    from has_api.infrastructure.database.models.identity import WorkspaceModel


class DatasetModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "datasets"

    workspace_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    workspace: Mapped["WorkspaceModel"] = relationship(back_populates="datasets")
    test_cases: Mapped[list["TestCaseModel"]] = relationship(
        back_populates="dataset",
        cascade="all, delete-orphan",
    )
    evaluation_runs: Mapped[list["EvaluationRunModel"]] = relationship(back_populates="dataset")


class TestCaseModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "test_cases"

    dataset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str | None] = mapped_column(Text)
    ground_truth: Mapped[str | None] = mapped_column(Text)
    external_id: Mapped[str | None] = mapped_column(String(255), index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_: Mapped[dict[str, object]] = mapped_column("metadata", JSONB, default=dict)

    dataset: Mapped["DatasetModel"] = relationship(back_populates="test_cases")
