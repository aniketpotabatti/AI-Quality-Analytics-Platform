"""Dataset and test-case endpoints — fully implemented."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from has_api.api.dependencies.auth import WorkspaceAccess, get_workspace_access, require_roles
from has_api.api.dependencies.repos import ReposDep
from has_api.api.schemas.common import MessageResponse, Page, ProblemDetail
from has_api.api.schemas.datasets import (
    DatasetCreate,
    DatasetResponse,
    DatasetUpdate,
    TestCaseBulkCreate,
    TestCaseBulkCreateResponse,
    TestCaseCreate,
    TestCaseResponse,
    TestCaseUpdate,
)
from has_api.api.schemas.enums import WorkspaceRole
from has_api.api.deps import PaginationParams
from has_api.application.use_cases import datasets as ds_uc
from has_api.domain.exceptions import DomainError, NotFoundError

router = APIRouter(
    prefix="/workspaces/{workspace_id}/datasets",
    tags=["datasets"],
)

_ERRORS = {
    401: {"model": ProblemDetail},
    403: {"model": ProblemDetail},
    404: {"model": ProblemDetail},
    422: {"model": ProblemDetail},
}

_WRITE = Depends(
    require_roles(WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.MEMBER)
)
_READ = Depends(get_workspace_access)


def _domain_error_to_http(exc: DomainError) -> HTTPException:
    if isinstance(exc, NotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"type": "about:blank", "title": "Not Found", "status": 404,
                    "detail": exc.message, "code": exc.code},
        )
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"type": "about:blank", "title": "Bad Request", "status": 400,
                "detail": exc.message, "code": exc.code},
    )


@router.get(
    "",
    response_model=Page[DatasetResponse],
    summary="List datasets in a workspace",
    responses=_ERRORS,
)
async def list_datasets(
    access: Annotated[WorkspaceAccess, _READ],
    pagination: Annotated[PaginationParams, Depends()],
    repos: ReposDep,
) -> Page[DatasetResponse]:
    items, total = await ds_uc.list_datasets(
        workspace_id=access.workspace_id,
        limit=pagination.limit,
        offset=pagination.offset,
        datasets=repos.datasets,
    )
    return Page(
        items=[DatasetResponse.model_validate(d, from_attributes=True) for d in items],
        pagination=pagination.to_meta(total),
    )


@router.post(
    "",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a dataset",
    responses=_ERRORS,
)
async def create_dataset(
    body: DatasetCreate,
    access: Annotated[WorkspaceAccess, _WRITE],
    repos: ReposDep,
) -> DatasetResponse:
    ds = await ds_uc.create_dataset(
        workspace_id=access.workspace_id,
        name=body.name,
        description=body.description,
        created_by_id=access.principal.user_id,  # type: ignore[arg-type]
        datasets=repos.datasets,
    )
    return DatasetResponse.model_validate(ds, from_attributes=True)


@router.get(
    "/{dataset_id}",
    response_model=DatasetResponse,
    summary="Get dataset detail",
    responses=_ERRORS,
)
async def get_dataset(
    dataset_id: UUID,
    access: Annotated[WorkspaceAccess, _READ],
    repos: ReposDep,
) -> DatasetResponse:
    try:
        ds = await ds_uc.get_dataset(
            workspace_id=access.workspace_id,
            dataset_id=dataset_id,
            datasets=repos.datasets,
        )
    except DomainError as exc:
        raise _domain_error_to_http(exc) from exc
    return DatasetResponse.model_validate(ds, from_attributes=True)


@router.patch(
    "/{dataset_id}",
    response_model=DatasetResponse,
    summary="Update dataset metadata",
    responses=_ERRORS,
)
async def update_dataset(
    dataset_id: UUID,
    body: DatasetUpdate,
    access: Annotated[WorkspaceAccess, _WRITE],
    repos: ReposDep,
) -> DatasetResponse:
    try:
        ds = await ds_uc.update_dataset(
            workspace_id=access.workspace_id,
            dataset_id=dataset_id,
            name=body.name,
            description=body.description,
            datasets=repos.datasets,
        )
    except DomainError as exc:
        raise _domain_error_to_http(exc) from exc
    return DatasetResponse.model_validate(ds, from_attributes=True)


@router.delete(
    "/{dataset_id}",
    response_model=MessageResponse,
    summary="Delete a dataset and its test cases",
    responses=_ERRORS,
)
async def delete_dataset(
    dataset_id: UUID,
    access: Annotated[
        WorkspaceAccess,
        Depends(require_roles(WorkspaceRole.OWNER, WorkspaceRole.ADMIN)),
    ],
    repos: ReposDep,
) -> MessageResponse:
    try:
        await ds_uc.delete_dataset(
            workspace_id=access.workspace_id,
            dataset_id=dataset_id,
            datasets=repos.datasets,
        )
    except DomainError as exc:
        raise _domain_error_to_http(exc) from exc
    return MessageResponse(message="Dataset deleted")


# ── Test cases ────────────────────────────────────────────────────────────────


@router.get(
    "/{dataset_id}/test-cases",
    response_model=Page[TestCaseResponse],
    summary="List test cases in a dataset",
    responses=_ERRORS,
    tags=["datasets", "test-cases"],
)
async def list_test_cases(
    dataset_id: UUID,
    access: Annotated[WorkspaceAccess, _READ],
    pagination: Annotated[PaginationParams, Depends()],
    repos: ReposDep,
) -> Page[TestCaseResponse]:
    # Verify dataset belongs to workspace
    try:
        await ds_uc.get_dataset(
            workspace_id=access.workspace_id,
            dataset_id=dataset_id,
            datasets=repos.datasets,
        )
    except DomainError as exc:
        raise _domain_error_to_http(exc) from exc

    items, total = await ds_uc.list_test_cases(
        dataset_id=dataset_id,
        limit=pagination.limit,
        offset=pagination.offset,
        test_cases=repos.test_cases,
    )
    return Page(
        items=[TestCaseResponse.model_validate(tc, from_attributes=True) for tc in items],
        pagination=pagination.to_meta(total),
    )


@router.post(
    "/{dataset_id}/test-cases",
    response_model=TestCaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a single test case",
    responses=_ERRORS,
    tags=["datasets", "test-cases"],
)
async def create_test_case(
    dataset_id: UUID,
    body: TestCaseCreate,
    access: Annotated[WorkspaceAccess, _WRITE],
    repos: ReposDep,
) -> TestCaseResponse:
    try:
        await ds_uc.get_dataset(
            workspace_id=access.workspace_id,
            dataset_id=dataset_id,
            datasets=repos.datasets,
        )
    except DomainError as exc:
        raise _domain_error_to_http(exc) from exc

    tc = await ds_uc.create_test_case(
        dataset_id=dataset_id,
        prompt=body.prompt,
        response=body.response,
        context=body.context,
        ground_truth=body.ground_truth,
        external_id=body.external_id,
        sort_order=body.sort_order,
        metadata=body.metadata,
        test_cases=repos.test_cases,
    )
    return TestCaseResponse.model_validate(tc, from_attributes=True)


@router.post(
    "/{dataset_id}/test-cases/bulk",
    response_model=TestCaseBulkCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk-create test cases (max 1000)",
    responses=_ERRORS,
    tags=["datasets", "test-cases"],
)
async def bulk_create_test_cases(
    dataset_id: UUID,
    body: TestCaseBulkCreate,
    access: Annotated[WorkspaceAccess, _WRITE],
    repos: ReposDep,
) -> TestCaseBulkCreateResponse:
    try:
        await ds_uc.get_dataset(
            workspace_id=access.workspace_id,
            dataset_id=dataset_id,
            datasets=repos.datasets,
        )
    except DomainError as exc:
        raise _domain_error_to_http(exc) from exc

    tcs = await ds_uc.bulk_create_test_cases(
        dataset_id=dataset_id,
        items=[item.model_dump() for item in body.items],
        test_cases=repos.test_cases,
    )
    return TestCaseBulkCreateResponse(
        created=len(tcs),
        items=[TestCaseResponse.model_validate(tc, from_attributes=True) for tc in tcs],
    )


@router.get(
    "/{dataset_id}/test-cases/{test_case_id}",
    response_model=TestCaseResponse,
    summary="Get a test case",
    responses=_ERRORS,
    tags=["datasets", "test-cases"],
)
async def get_test_case(
    dataset_id: UUID,
    test_case_id: UUID,
    access: Annotated[WorkspaceAccess, _READ],
    repos: ReposDep,
) -> TestCaseResponse:
    try:
        tc = await ds_uc.get_test_case(
            dataset_id=dataset_id,
            test_case_id=test_case_id,
            test_cases=repos.test_cases,
        )
    except DomainError as exc:
        raise _domain_error_to_http(exc) from exc
    return TestCaseResponse.model_validate(tc, from_attributes=True)


@router.patch(
    "/{dataset_id}/test-cases/{test_case_id}",
    response_model=TestCaseResponse,
    summary="Update a test case",
    responses=_ERRORS,
    tags=["datasets", "test-cases"],
)
async def update_test_case(
    dataset_id: UUID,
    test_case_id: UUID,
    body: TestCaseUpdate,
    access: Annotated[WorkspaceAccess, _WRITE],
    repos: ReposDep,
) -> TestCaseResponse:
    try:
        tc = await ds_uc.update_test_case(
            dataset_id=dataset_id,
            test_case_id=test_case_id,
            updates=body.model_dump(exclude_unset=True),
            test_cases=repos.test_cases,
        )
    except DomainError as exc:
        raise _domain_error_to_http(exc) from exc
    return TestCaseResponse.model_validate(tc, from_attributes=True)


@router.delete(
    "/{dataset_id}/test-cases/{test_case_id}",
    response_model=MessageResponse,
    summary="Delete a test case",
    responses=_ERRORS,
    tags=["datasets", "test-cases"],
)
async def delete_test_case(
    dataset_id: UUID,
    test_case_id: UUID,
    access: Annotated[WorkspaceAccess, _WRITE],
    repos: ReposDep,
) -> MessageResponse:
    try:
        await ds_uc.delete_test_case(
            dataset_id=dataset_id,
            test_case_id=test_case_id,
            test_cases=repos.test_cases,
        )
    except DomainError as exc:
        raise _domain_error_to_http(exc) from exc
    return MessageResponse(message="Test case deleted")
