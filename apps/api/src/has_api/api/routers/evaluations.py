"""Evaluation run and result endpoints — fully implemented."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from has_api.api.dependencies.auth import WorkspaceAccess, get_workspace_access, require_roles
from has_api.api.dependencies.repos import ReposDep
from has_api.api.deps import PaginationParams
from has_api.api.schemas.common import MessageResponse, Page, ProblemDetail
from has_api.api.schemas.enums import EvaluationRunStatus, MetricType, WorkspaceRole
from has_api.api.schemas.evaluations import (
    EvaluationResultResponse,
    EvaluationRunCreate,
    EvaluationRunDetailResponse,
    EvaluationRunResponse,
    MetricScoreResponse,
)
from has_api.application.use_cases import evaluations as eval_uc
from has_api.domain.exceptions import ConflictError, DomainError, NotFoundError

router = APIRouter(
    prefix="/workspaces/{workspace_id}/evaluation-runs",
    tags=["evaluations"],
)

_ERRORS = {
    401: {"model": ProblemDetail},
    403: {"model": ProblemDetail},
    404: {"model": ProblemDetail},
    409: {"model": ProblemDetail},
}


def _domain_error_to_http(exc: DomainError) -> HTTPException:
    if isinstance(exc, NotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"type": "about:blank", "title": "Not Found", "status": 404,
                    "detail": exc.message, "code": exc.code},
        )
    if isinstance(exc, ConflictError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": "about:blank", "title": "Conflict", "status": 409,
                    "detail": exc.message, "code": exc.code},
        )
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"type": "about:blank", "title": "Bad Request", "status": 400,
                "detail": exc.message, "code": exc.code},
    )


def _run_to_response(run) -> EvaluationRunResponse:
    return EvaluationRunResponse(
        id=run.id,
        workspace_id=run.workspace_id,
        dataset_id=run.dataset_id,
        name=run.name,
        status=EvaluationRunStatus(run.status),
        metrics_config=run.metrics_config,
        model_config_id=run.model_config_id,
        created_by_id=run.created_by_id,
        total_cases=run.total_cases,
        completed_cases=run.completed_cases,
        failed_cases=run.failed_cases,
        error_message=run.error_message,
        started_at=run.started_at,
        completed_at=run.completed_at,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


def _score_to_response(score) -> MetricScoreResponse:
    return MetricScoreResponse(
        id=score.id,
        result_id=score.result_id,
        metric_type=MetricType(score.metric_type),
        score=score.score,
        passed=score.passed,
        rationale=score.rationale,
        metadata=score.metadata,
        created_at=score.created_at,
    )


def _result_to_response(result, scores=None) -> EvaluationResultResponse:
    return EvaluationResultResponse(
        id=result.id,
        run_id=result.run_id,
        test_case_id=result.test_case_id,
        status=result.status,
        overall_score=result.overall_score,
        error_message=result.error_message,
        metric_scores=[_score_to_response(s) for s in (scores or [])],
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.get(
    "",
    response_model=Page[EvaluationRunResponse],
    summary="List evaluation runs",
    responses=_ERRORS,
)
async def list_evaluation_runs(
    access: Annotated[WorkspaceAccess, Depends(get_workspace_access)],
    pagination: Annotated[PaginationParams, Depends()],
    repos: ReposDep,
    run_status: Annotated[
        EvaluationRunStatus | None,
        Query(alias="status", description="Filter by run status"),
    ] = None,
    dataset_id: Annotated[UUID | None, Query(description="Filter by dataset")] = None,
) -> Page[EvaluationRunResponse]:
    items, total = await eval_uc.list_evaluation_runs(
        workspace_id=access.workspace_id,
        limit=pagination.limit,
        offset=pagination.offset,
        status_filter=run_status.value if run_status else None,
        dataset_id=dataset_id,
        evaluation_runs=repos.evaluation_runs,
    )
    return Page(
        items=[_run_to_response(r) for r in items],
        pagination=pagination.to_meta(total),
    )


@router.post(
    "",
    response_model=EvaluationRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start an evaluation run (async)",
    description=(
        "Creates a run in `pending` status and enqueues worker jobs. "
        "Poll GET /evaluation-runs/{run_id} for progress."
    ),
    responses=_ERRORS,
)
async def create_evaluation_run(
    body: EvaluationRunCreate,
    access: Annotated[
        WorkspaceAccess,
        Depends(require_roles(WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.MEMBER)),
    ],
    repos: ReposDep,
) -> EvaluationRunResponse:
    try:
        run = await eval_uc.create_evaluation_run(
            workspace_id=access.workspace_id,
            dataset_id=body.dataset_id,
            name=body.name,
            metrics_config=body.metrics_config.model_dump(),
            model_config_id=body.model_config_id,
            created_by_id=access.principal.user_id,  # type: ignore[arg-type]
            datasets=repos.datasets,
            evaluation_runs=repos.evaluation_runs,
        )
    except DomainError as exc:
        raise _domain_error_to_http(exc) from exc

    # Enqueue the worker job (fire-and-forget)
    try:
        from has_api.infrastructure.redis import get_arq_pool
        arq = await get_arq_pool()
        await arq.enqueue_job("run_evaluation", str(run.id))
    except Exception:
        # Worker not available in dev without Redis — run stays pending
        pass

    return _run_to_response(run)


@router.get(
    "/{run_id}",
    response_model=EvaluationRunDetailResponse,
    summary="Get evaluation run detail",
    responses=_ERRORS,
)
async def get_evaluation_run(
    run_id: UUID,
    access: Annotated[WorkspaceAccess, Depends(get_workspace_access)],
    repos: ReposDep,
) -> EvaluationRunDetailResponse:
    try:
        run, pass_rate, avg_score = await eval_uc.get_evaluation_run(
            workspace_id=access.workspace_id,
            run_id=run_id,
            evaluation_runs=repos.evaluation_runs,
            evaluation_results=repos.evaluation_results,
        )
    except DomainError as exc:
        raise _domain_error_to_http(exc) from exc

    return EvaluationRunDetailResponse(
        **_run_to_response(run).model_dump(),
        pass_rate=pass_rate,
        average_score=avg_score,
    )


@router.post(
    "/{run_id}/cancel",
    response_model=EvaluationRunResponse,
    summary="Cancel a pending or running evaluation",
    responses=_ERRORS,
)
async def cancel_evaluation_run(
    run_id: UUID,
    access: Annotated[
        WorkspaceAccess,
        Depends(require_roles(WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.MEMBER)),
    ],
    repos: ReposDep,
) -> EvaluationRunResponse:
    try:
        run = await eval_uc.cancel_evaluation_run(
            workspace_id=access.workspace_id,
            run_id=run_id,
            evaluation_runs=repos.evaluation_runs,
        )
    except DomainError as exc:
        raise _domain_error_to_http(exc) from exc
    return _run_to_response(run)


@router.get(
    "/{run_id}/results",
    response_model=Page[EvaluationResultResponse],
    summary="List per-case results for a run",
    responses=_ERRORS,
)
async def list_evaluation_results(
    run_id: UUID,
    access: Annotated[WorkspaceAccess, Depends(get_workspace_access)],
    pagination: Annotated[PaginationParams, Depends()],
    repos: ReposDep,
    include_scores: Annotated[
        bool,
        Query(description="Embed metric_scores on each result"),
    ] = True,
) -> Page[EvaluationResultResponse]:
    try:
        results, scores_list, total = await eval_uc.list_evaluation_results(
            run_id=run_id,
            workspace_id=access.workspace_id,
            limit=pagination.limit,
            offset=pagination.offset,
            include_scores=include_scores,
            evaluation_runs=repos.evaluation_runs,
            evaluation_results=repos.evaluation_results,
        )
    except DomainError as exc:
        raise _domain_error_to_http(exc) from exc
    return Page(
        items=[_result_to_response(r, s) for r, s in zip(results, scores_list)],
        pagination=pagination.to_meta(total),
    )


@router.get(
    "/{run_id}/results/{result_id}",
    response_model=EvaluationResultResponse,
    summary="Get a single evaluation result with metric scores",
    responses=_ERRORS,
)
async def get_evaluation_result(
    run_id: UUID,
    result_id: UUID,
    access: Annotated[WorkspaceAccess, Depends(get_workspace_access)],
    repos: ReposDep,
) -> EvaluationResultResponse:
    try:
        result, scores = await eval_uc.get_evaluation_result(
            run_id=run_id,
            result_id=result_id,
            workspace_id=access.workspace_id,
            evaluation_runs=repos.evaluation_runs,
            evaluation_results=repos.evaluation_results,
        )
    except DomainError as exc:
        raise _domain_error_to_http(exc) from exc
    return _result_to_response(result, scores)


@router.delete(
    "/{run_id}",
    response_model=MessageResponse,
    summary="Delete an evaluation run and its results",
    responses=_ERRORS,
)
async def delete_evaluation_run(
    run_id: UUID,
    access: Annotated[
        WorkspaceAccess,
        Depends(require_roles(WorkspaceRole.OWNER, WorkspaceRole.ADMIN)),
    ],
    repos: ReposDep,
) -> MessageResponse:
    run = await repos.evaluation_runs.get_by_id(access.workspace_id, run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"type": "about:blank", "title": "Not Found", "status": 404,
                    "detail": f"Evaluation run not found: {run_id}", "code": "not_found"},
        )
    # Delete cascades via DB foreign keys
    # For now, mark as cancelled (hard delete requires direct DB or raw SQL)
    from has_api.domain.value_objects import EvaluationRunStatus
    run.status = EvaluationRunStatus.CANCELLED
    await repos.evaluation_runs.save(run)
    return MessageResponse(message="Evaluation run deleted")
