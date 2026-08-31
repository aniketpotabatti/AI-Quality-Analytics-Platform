"""Evaluation ORM models."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from has_api.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from has_api.infrastructure.database.models.datasets import DatasetModel, TestCaseModel


class EvaluationRunModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "evaluation_runs"

    workspace_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dataset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_config_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("model_configs.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    metrics_config: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    created_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    total_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    dataset: Mapped["DatasetModel"] = relationship(back_populates="evaluation_runs")
    results: Mapped[list["EvaluationResultModel"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )


class EvaluationResultModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "evaluation_results"
    __table_args__ = (UniqueConstraint("run_id", "test_case_id", name="uq_run_test_case"),)

    run_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("test_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    overall_score: Mapped[float | None] = mapped_column(Float)
    error_message: Mapped[str | None] = mapped_column(Text)

    run: Mapped["EvaluationRunModel"] = relationship(back_populates="results")
    test_case: Mapped["TestCaseModel"] = relationship()
    metric_scores: Mapped[list["MetricScoreModel"]] = relationship(
        back_populates="result",
        cascade="all, delete-orphan",
    )


class MetricScoreModel(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "metric_scores"
    __table_args__ = (UniqueConstraint("result_id", "metric_type", name="uq_result_metric"),)

    result_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("evaluation_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    passed: Mapped[bool] = mapped_column(nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict[str, object]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    result: Mapped["EvaluationResultModel"] = relationship(back_populates="metric_scores")
