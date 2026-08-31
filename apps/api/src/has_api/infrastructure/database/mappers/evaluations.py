"""Maps evaluation ORM models to domain entities."""

from has_api.domain.entities import EvaluationResult, EvaluationRun, MetricScore
from has_api.domain.value_objects import EvaluationResultStatus, EvaluationRunStatus, MetricType
from has_api.infrastructure.database.models.evaluations import (
    EvaluationResultModel,
    EvaluationRunModel,
    MetricScoreModel,
)


def evaluation_run_to_domain(model: EvaluationRunModel) -> EvaluationRun:
    if model.created_by_id is None:
        msg = "EvaluationRunModel.created_by_id is required for domain mapping"
        raise ValueError(msg)
    return EvaluationRun(
        id=model.id,
        workspace_id=model.workspace_id,
        dataset_id=model.dataset_id,
        name=model.name,
        status=EvaluationRunStatus(model.status),
        metrics_config=model.metrics_config or {},
        model_config_id=model.model_config_id,
        created_by_id=model.created_by_id,
        total_cases=model.total_cases,
        completed_cases=model.completed_cases,
        failed_cases=model.failed_cases,
        error_message=model.error_message,
        started_at=model.started_at,
        completed_at=model.completed_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def evaluation_run_to_orm(
    domain: EvaluationRun,
    model: EvaluationRunModel | None = None,
) -> EvaluationRunModel:
    if model is None:
        model = EvaluationRunModel(id=domain.id)
    model.workspace_id = domain.workspace_id
    model.dataset_id = domain.dataset_id
    model.name = domain.name
    model.status = domain.status.value
    model.metrics_config = domain.metrics_config
    model.model_config_id = domain.model_config_id
    model.created_by_id = domain.created_by_id
    model.total_cases = domain.total_cases
    model.completed_cases = domain.completed_cases
    model.failed_cases = domain.failed_cases
    model.error_message = domain.error_message
    model.started_at = domain.started_at
    model.completed_at = domain.completed_at
    model.created_at = domain.created_at
    model.updated_at = domain.updated_at
    return model


def evaluation_result_to_domain(model: EvaluationResultModel) -> EvaluationResult:
    return EvaluationResult(
        id=model.id,
        run_id=model.run_id,
        test_case_id=model.test_case_id,
        status=EvaluationResultStatus(model.status),
        overall_score=model.overall_score,
        error_message=model.error_message,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def evaluation_result_to_orm(
    domain: EvaluationResult,
    model: EvaluationResultModel | None = None,
) -> EvaluationResultModel:
    if model is None:
        model = EvaluationResultModel(id=domain.id)
    model.run_id = domain.run_id
    model.test_case_id = domain.test_case_id
    model.status = domain.status.value
    model.overall_score = domain.overall_score
    model.error_message = domain.error_message
    model.created_at = domain.created_at
    model.updated_at = domain.updated_at
    return model


def metric_score_to_domain(model: MetricScoreModel) -> MetricScore:
    return MetricScore(
        id=model.id,
        result_id=model.result_id,
        metric_type=MetricType(model.metric_type),
        score=model.score,
        passed=model.passed,
        rationale=model.rationale,
        metadata=model.metadata_ or {},
        created_at=model.created_at,
    )


def metric_score_to_orm(
    domain: MetricScore,
    model: MetricScoreModel | None = None,
) -> MetricScoreModel:
    if model is None:
        model = MetricScoreModel(id=domain.id)
    model.result_id = domain.result_id
    model.metric_type = domain.metric_type.value
    model.score = domain.score
    model.passed = domain.passed
    model.rationale = domain.rationale
    model.metadata_ = domain.metadata
    model.created_at = domain.created_at
    return model
