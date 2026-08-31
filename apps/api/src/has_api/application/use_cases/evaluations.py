"""Evaluation run use cases."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from has_api.application.ports.repositories import (
    DatasetRepository,
    EvaluationResultRepository,
    EvaluationRunRepository,
)
from has_api.domain.entities import EvaluationResult, EvaluationRun
from has_api.domain.exceptions import ConflictError, NotFoundError
from has_api.domain.value_objects import EvaluationResultStatus, EvaluationRunStatus


async def create_evaluation_run(
    *,
    workspace_id: UUID,
    dataset_id: UUID,
    name: str,
    metrics_config: dict,
    model_config_id: UUID | None,
    created_by_id: UUID,
    datasets: DatasetRepository,
    evaluation_runs: EvaluationRunRepository,
) -> EvaluationRun:
    """Create a run record and return it (worker enqueues the actual work)."""
    # Verify dataset exists in workspace
    ds = await datasets.get_by_id(workspace_id, dataset_id)
    if ds is None:
        raise NotFoundError("dataset", dataset_id)

    run = EvaluationRun(
        workspace_id=workspace_id,
        dataset_id=dataset_id,
        name=name,
        metrics_config=metrics_config,
        model_config_id=model_config_id,
        created_by_id=created_by_id,
        status=EvaluationRunStatus.PENDING,
    )
    return await evaluation_runs.save(run)


async def get_evaluation_run(
    *,
    workspace_id: UUID,
    run_id: UUID,
    evaluation_runs: EvaluationRunRepository,
    evaluation_results: EvaluationResultRepository,
) -> tuple[EvaluationRun, float | None, float | None]:
    """Return run + pass_rate + average_score."""
    run = await evaluation_runs.get_by_id(workspace_id, run_id)
    if run is None:
        raise NotFoundError("evaluation_run", run_id)

    # Compute summary stats from results
    results = await evaluation_results.list_by_run(run_id, limit=10000)
    pass_rate = None
    average_score = None
    completed = [r for r in results if r.status == EvaluationResultStatus.COMPLETED]
    if completed:
        scored = [r for r in completed if r.overall_score is not None]
        if scored:
            average_score = sum(r.overall_score for r in scored) / len(scored)  # type: ignore[misc]
            pass_rate = sum(1 for r in scored if (r.overall_score or 0) >= 0.5) / len(scored)

    return run, pass_rate, average_score


async def list_evaluation_runs(
    *,
    workspace_id: UUID,
    limit: int,
    offset: int,
    status_filter: str | None,
    dataset_id: UUID | None,
    evaluation_runs: EvaluationRunRepository,
) -> tuple[list[EvaluationRun], int]:
    items = await evaluation_runs.list_by_workspace(
        workspace_id,
        limit=limit,
        offset=offset,
        status_filter=status_filter,
        dataset_id=dataset_id,
    )
    total = await evaluation_runs.count_by_workspace(
        workspace_id,
        status_filter=status_filter,
        dataset_id=dataset_id,
    )
    return items, total


async def cancel_evaluation_run(
    *,
    workspace_id: UUID,
    run_id: UUID,
    evaluation_runs: EvaluationRunRepository,
) -> EvaluationRun:
    run = await evaluation_runs.get_by_id(workspace_id, run_id)
    if run is None:
        raise NotFoundError("evaluation_run", run_id)
    if run.status not in (EvaluationRunStatus.PENDING, EvaluationRunStatus.RUNNING):
        raise ConflictError(
            "invalid_state",
            f"Cannot cancel a run with status '{run.status}'",
        )
    run.status = EvaluationRunStatus.CANCELLED
    run.completed_at = datetime.now(UTC)
    return await evaluation_runs.save(run)


async def delete_evaluation_run(
    *,
    workspace_id: UUID,
    run_id: UUID,
    evaluation_runs: EvaluationRunRepository,
) -> None:
    run = await evaluation_runs.get_by_id(workspace_id, run_id)
    if run is None:
        raise NotFoundError("evaluation_run", run_id)
    # Soft-delete: mark as cancelled; hard delete via cascade in DB
    # For now we just verify it exists; router handles the delete
    # (EvaluationRunRepository doesn't have delete yet — we do it inline)


async def list_evaluation_results(
    *,
    run_id: UUID,
    workspace_id: UUID,
    limit: int,
    offset: int,
    include_scores: bool,
    evaluation_runs: EvaluationRunRepository,
    evaluation_results: EvaluationResultRepository,
) -> tuple[list[EvaluationResult], list[list], int]:
    """Return (results, scores_per_result, total)."""
    run = await evaluation_runs.get_by_id(workspace_id, run_id)
    if run is None:
        raise NotFoundError("evaluation_run", run_id)

    results = await evaluation_results.list_by_run(run_id, limit=limit, offset=offset)
    total = await evaluation_results.count_by_run(run_id)

    scores_list = []
    for result in results:
        if include_scores:
            scores = await evaluation_results.list_scores_for_result(result.id)
        else:
            scores = []
        scores_list.append(scores)

    return results, scores_list, total


async def get_evaluation_result(
    *,
    run_id: UUID,
    result_id: UUID,
    workspace_id: UUID,
    evaluation_runs: EvaluationRunRepository,
    evaluation_results: EvaluationResultRepository,
) -> tuple[EvaluationResult, list]:
    run = await evaluation_runs.get_by_id(workspace_id, run_id)
    if run is None:
        raise NotFoundError("evaluation_run", run_id)

    result = await evaluation_results.get_by_id(run_id, result_id)
    if result is None:
        raise NotFoundError("evaluation_result", result_id)

    scores = await evaluation_results.list_scores_for_result(result_id)
    return result, scores
