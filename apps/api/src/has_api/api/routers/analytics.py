"""Analytics aggregation endpoints."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from has_api.api.dependencies.auth import WorkspaceAccess, get_workspace_access
from has_api.api.dependencies.repos import ReposDep
from has_api.api.schemas.analytics import (
    EvaluationRunComparisonItem,
    EvaluationRunComparisonResponse,
    RunStatusCount,
    WorkspaceSummaryResponse,
    WorkspaceTrendsResponse,
)
from has_api.api.schemas.common import ProblemDetail
from has_api.api.schemas.enums import EvaluationRunStatus
from has_api.domain.value_objects import EvaluationRunStatus as DomainRunStatus

router = APIRouter(
    prefix="/workspaces/{workspace_id}/analytics",
    tags=["analytics"],
)

_ERRORS = {
    401: {"model": ProblemDetail},
    403: {"model": ProblemDetail},
}


@router.get(
    "/summary",
    response_model=WorkspaceSummaryResponse,
    summary="Workspace-level evaluation summary",
    responses=_ERRORS,
)
async def workspace_summary(
    access: Annotated[WorkspaceAccess, Depends(get_workspace_access)],
    repos: ReposDep,
) -> WorkspaceSummaryResponse:
    ws_id = access.workspace_id

    dataset_count = await repos.datasets.count_by_workspace(ws_id)
    run_count = await repos.evaluation_runs.count_by_workspace(ws_id)
    completed_count = await repos.evaluation_runs.count_by_workspace(
        ws_id, status_filter=DomainRunStatus.COMPLETED
    )

    # Test case count (sum across all datasets — approximate with runs for now)
    runs = await repos.evaluation_runs.list_by_workspace(ws_id, limit=1000)
    test_case_count = sum(r.total_cases for r in runs)

    return WorkspaceSummaryResponse(
        workspace_id=ws_id,
        dataset_count=dataset_count,
        test_case_count=test_case_count,
        evaluation_run_count=run_count,
        completed_run_count=completed_count,
        average_pass_rate=None,  # Computed from results in Phase 7
    )


@router.get(
    "/trends",
    response_model=WorkspaceTrendsResponse,
    summary="Metric trends and run status breakdown",
    responses=_ERRORS,
)
async def workspace_trends(
    access: Annotated[WorkspaceAccess, Depends(get_workspace_access)],
    repos: ReposDep,
    from_date: Annotated[datetime | None, Query(alias="from")] = None,
    to_date: Annotated[datetime | None, Query(alias="to")] = None,
) -> WorkspaceTrendsResponse:
    ws_id = access.workspace_id

    # Count runs by status
    status_counts = []
    for status_val in DomainRunStatus:
        count = await repos.evaluation_runs.count_by_workspace(
            ws_id, status_filter=status_val.value
        )
        if count > 0:
            status_counts.append(
                RunStatusCount(status=EvaluationRunStatus(status_val.value), count=count)
            )

    return WorkspaceTrendsResponse(
        workspace_id=ws_id,
        from_date=from_date,
        to_date=to_date,
        runs_by_status=status_counts,
        metrics=[],  # Full metric aggregation in Phase 7
    )


@router.get(
    "/compare-runs",
    response_model=EvaluationRunComparisonResponse,
    summary="Compare selected evaluation runs",
    responses=_ERRORS,
)
async def compare_runs(
    access: Annotated[WorkspaceAccess, Depends(get_workspace_access)],
    repos: ReposDep,
    run_ids: Annotated[
        list[UUID],
        Query(min_length=1, max_length=20, description="Run IDs to compare"),
    ] = [],
) -> EvaluationRunComparisonResponse:
    items = []
    for run_id in run_ids:
        run = await repos.evaluation_runs.get_by_id(access.workspace_id, run_id)
        if run:
            items.append(EvaluationRunComparisonItem(
                run_id=run.id,
                name=run.name,
                status=EvaluationRunStatus(run.status),
                average_score=None,
                pass_rate=None,
                completed_at=run.completed_at,
            ))
    return EvaluationRunComparisonResponse(
        workspace_id=access.workspace_id,
        items=items,
    )
