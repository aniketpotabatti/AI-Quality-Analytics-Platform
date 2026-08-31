"""Evaluations bounded context entities."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from has_api.domain.value_objects import EvaluationResultStatus, EvaluationRunStatus, MetricType


@dataclass(kw_only=True)
class EvaluationRun:
    id: UUID = field(default_factory=uuid4)
    workspace_id: UUID
    dataset_id: UUID
    name: str
    status: EvaluationRunStatus = EvaluationRunStatus.PENDING
    metrics_config: dict[str, object] = field(default_factory=dict)
    model_config_id: UUID | None = None
    created_by_id: UUID
    total_cases: int = 0
    completed_cases: int = 0
    failed_cases: int = 0
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(kw_only=True)
class EvaluationResult:
    id: UUID = field(default_factory=uuid4)
    run_id: UUID
    test_case_id: UUID
    status: EvaluationResultStatus = EvaluationResultStatus.PENDING
    overall_score: float | None = None
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(kw_only=True)
class MetricScore:
    id: UUID = field(default_factory=uuid4)
    result_id: UUID
    metric_type: MetricType
    score: float
    passed: bool
    rationale: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
