"""Model registry endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from has_api.api.dependencies.auth import WorkspaceAccess, get_workspace_access, require_roles
from has_api.api.deps import PaginationParams, not_implemented
from has_api.api.schemas.common import MessageResponse, Page, ProblemDetail
from has_api.api.schemas.enums import WorkspaceRole
from has_api.api.schemas.models import (
    ModelConfigCreate,
    ModelConfigResponse,
    ModelConfigUpdate,
)

router = APIRouter(
    prefix="/workspaces/{workspace_id}/model-configs",
    tags=["model-registry"],
)

_ERRORS = {
    401: {"model": ProblemDetail},
    403: {"model": ProblemDetail},
    404: {"model": ProblemDetail},
    501: {"model": ProblemDetail},
}


@router.get(
    "",
    response_model=Page[ModelConfigResponse],
    summary="List model configurations",
    responses=_ERRORS,
)
async def list_model_configs(
    _access: Annotated[WorkspaceAccess, Depends(get_workspace_access)],
    _pagination: Annotated[PaginationParams, Depends()],
) -> Page[ModelConfigResponse]:
    not_implemented("List model configs")
    raise AssertionError  # pragma: no cover


@router.post(
    "",
    response_model=ModelConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a model configuration",
    responses=_ERRORS,
)
async def create_model_config(
    _body: ModelConfigCreate,
    _access: Annotated[
        WorkspaceAccess,
        Depends(require_roles(WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.MEMBER)),
    ],
) -> ModelConfigResponse:
    not_implemented("Create model config")
    raise AssertionError  # pragma: no cover


@router.get(
    "/{config_id}",
    response_model=ModelConfigResponse,
    summary="Get model configuration",
    responses=_ERRORS,
)
async def get_model_config(
    _config_id: UUID,
    _access: Annotated[WorkspaceAccess, Depends(get_workspace_access)],
) -> ModelConfigResponse:
    not_implemented("Get model config")
    raise AssertionError  # pragma: no cover


@router.patch(
    "/{config_id}",
    response_model=ModelConfigResponse,
    summary="Update model configuration",
    responses=_ERRORS,
)
async def update_model_config(
    _config_id: UUID,
    _body: ModelConfigUpdate,
    _access: Annotated[
        WorkspaceAccess,
        Depends(require_roles(WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.MEMBER)),
    ],
) -> ModelConfigResponse:
    not_implemented("Update model config")
    raise AssertionError  # pragma: no cover


@router.delete(
    "/{config_id}",
    response_model=MessageResponse,
    summary="Delete model configuration",
    responses=_ERRORS,
)
async def delete_model_config(
    _config_id: UUID,
    _access: Annotated[
        WorkspaceAccess,
        Depends(require_roles(WorkspaceRole.OWNER, WorkspaceRole.ADMIN)),
    ],
) -> MessageResponse:
    not_implemented("Delete model config")
    raise AssertionError  # pragma: no cover
