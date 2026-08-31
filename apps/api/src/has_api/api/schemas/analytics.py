"""Analytics aggregation DTOs (read-only)."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from has_api.api.schemas.common import APIModel
from has_api.api.schemas.enums import EvaluationRunStatus, MetricType


class WorkspaceSummaryResponse(APIModel):
    workspace_id: UUID
    dataset_count: int
    test_case_count: int
    evaluation_run_count: int
    completed_run_count: int
    average_pass_rate: float | None = Field(
        default=None,
        description="Mean pass rate across completed runs, if any",
    )


class MetricAggregate(APIModel):
    metric_type: MetricType
    average_score: float
    pass_rate: float
    sample_count: int


class RunStatusCount(APIModel):
    status: EvaluationRunStatus
    count: int


class WorkspaceTrendsResponse(APIModel):
    workspace_id: UUID
    from_date: datetime | None = None
    to_date: datetime | None = None
    runs_by_status: list[RunStatusCount]
    metrics: list[MetricAggregate]


class EvaluationRunComparisonItem(APIModel):
    run_id: UUID
    name: str
    status: EvaluationRunStatus
    average_score: float | None = None
    pass_rate: float | None = None
    completed_at: datetime | None = None


class EvaluationRunComparisonResponse(APIModel):
    workspace_id: UUID
    items: list[EvaluationRunComparisonItem]
