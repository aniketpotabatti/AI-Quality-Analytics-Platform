"""Evaluation run, result, and metric-score DTOs."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from has_api.api.schemas.common import APIModel, TimestampedMixin, WorkspaceScopedMixin
from has_api.api.schemas.enums import (
    EvaluationResultStatus,
    EvaluationRunStatus,
    MetricType,
)


class MetricsConfig(APIModel):
    """Which metrics to run and optional per-metric thresholds."""

    metrics: list[MetricType] = Field(
        min_length=1,
        description="Ordered list of metrics to evaluate",
    )
    thresholds: dict[str, float] = Field(
        default_factory=dict,
        description="Optional pass thresholds keyed by metric type",
    )
    options: dict[str, Any] = Field(
        default_factory=dict,
        description="Metric-specific options (e.g. judge model overrides)",
    )


class EvaluationRunCreate(APIModel):
    name: str = Field(min_length=1, max_length=255)
    dataset_id: UUID
    metrics_config: MetricsConfig
    model_config_id: UUID | None = Field(
        default=None,
        description="Optional model config used for LLM-as-judge / generation",
    )


class EvaluationRunResponse(WorkspaceScopedMixin, TimestampedMixin):
    id: UUID
    dataset_id: UUID
    name: str
    status: EvaluationRunStatus
    metrics_config: dict[str, Any]
    model_config_id: UUID | None = None
    created_by_id: UUID | None = None
    total_cases: int
    completed_cases: int
    failed_cases: int
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class MetricScoreResponse(APIModel):
    id: UUID
    result_id: UUID
    metric_type: MetricType
    score: float
    passed: bool
    rationale: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class EvaluationResultResponse(TimestampedMixin):
    id: UUID
    run_id: UUID
    test_case_id: UUID
    status: EvaluationResultStatus
    overall_score: float | None = None
    error_message: str | None = None
    metric_scores: list[MetricScoreResponse] = Field(default_factory=list)


class EvaluationRunDetailResponse(EvaluationRunResponse):
    """Run detail with optional embedded summary stats."""

    pass_rate: float | None = Field(
        default=None,
        description="Fraction of completed cases with overall pass (when available)",
    )
    average_score: float | None = None
