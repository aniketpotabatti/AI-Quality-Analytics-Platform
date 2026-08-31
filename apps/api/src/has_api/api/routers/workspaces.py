"""Workspace and membership endpoints — fully implemented."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from has_api.api.dependencies.auth import (
    AuthenticatedPrincipal,
    WorkspaceAccess,
    get_current_principal,
    get_workspace_access,
    require_roles,
)
from has_api.api.dependencies.repos import ReposDep
from has_api.api.deps import PaginationParams
from has_api.api.schemas.common import MessageResponse, Page, ProblemDetail
from has_api.api.schemas.enums import WorkspaceRole
from has_api.api.schemas.workspaces import (
    WorkspaceCreate,
    WorkspaceMemberCreate,
    WorkspaceMemberResponse,
    WorkspaceMemberUpdate,
    WorkspaceResponse,
    WorkspaceUpdate,
)
from has_api.application.use_cases import workspaces as ws_uc
from has_api.domain.exceptions import DomainError, NotFoundError

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

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
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"type": "about:blank", "title": "Conflict", "status": 409,
                "detail": exc.message, "code": exc.code},
    )


@router.get(
    "",
    response_model=Page[WorkspaceResponse],
    summary="List workspaces for the current user",
    responses=_ERRORS,
)
async def list_workspaces(
    principal: Annotated[AuthenticatedPrincipal, Depends(get_current_principal)],
    pagination: Annotated[PaginationParams, Depends()],
    repos: ReposDep,
) -> Page[WorkspaceResponse]:
    if principal.user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    memberships = await repos.workspaces.list_memberships_for_user(principal.user_id)
    # Paginate in-memory for now (membership counts are typically small)
    start = pagination.offset
    end = start + pagination.limit
    page_memberships = memberships[start:end]

    items: list[WorkspaceResponse] = []
    for m in page_memberships:
        ws = await repos.workspaces.get_by_id(m.workspace_id)
        if ws:
            items.append(WorkspaceResponse(
                id=ws.id,
                name=ws.name,
                slug=ws.slug,
                created_at=ws.created_at,
                updated_at=ws.updated_at,
            ))

    return Page(items=items, pagination=pagination.to_meta(len(memberships)))


@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a workspace",
    responses=_ERRORS,
)
async def create_workspace(
    body: WorkspaceCreate,
    principal: Annotated[AuthenticatedPrincipal, Depends(get_current_principal)],
    repos: ReposDep,
) -> WorkspaceResponse:
    if principal.user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    try:
        ws = await ws_uc.create_workspace(
            name=body.name,
            slug=body.slug,
            created_by_id=principal.user_id,
            workspaces=repos.workspaces,
        )
    except DomainError as exc:
        raise _domain_error_to_http(exc) from exc
    return WorkspaceResponse(
        id=ws.id, name=ws.name, slug=ws.slug,
        created_at=ws.created_at, updated_at=ws.updated_at,
    )


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="Get workspace by ID",
    responses=_ERRORS,
)
async def get_workspace(
    workspace_id: UUID,
    access: Annotated[WorkspaceAccess, Depends(get_workspace_access)],
    repos: ReposDep,
) -> WorkspaceResponse:
    ws = await repos.workspaces.get_by_id(access.workspace_id)
    if ws is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return WorkspaceResponse(
        id=ws.id, name=ws.name, slug=ws.slug,
        created_at=ws.created_at, updated_at=ws.updated_at,
    )


@router.patch(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="Update workspace",
    responses=_ERRORS,
)
async def update_workspace(
    body: WorkspaceUpdate,
    access: Annotated[
        WorkspaceAccess,
        Depends(require_roles(WorkspaceRole.OWNER, WorkspaceRole.ADMIN)),
    ],
    repos: ReposDep,
) -> WorkspaceResponse:
    try:
        ws = await ws_uc.update_workspace(
            workspace_id=access.workspace_id,
            name=body.name,
            workspaces=repos.workspaces,
        )
    except DomainError as exc:
        raise _domain_error_to_http(exc) from exc
    return WorkspaceResponse(
        id=ws.id, name=ws.name, slug=ws.slug,
        created_at=ws.created_at, updated_at=ws.updated_at,
    )


@router.get(
    "/{workspace_id}/members",
    response_model=Page[WorkspaceMemberResponse],
    summary="List workspace members",
    responses=_ERRORS,
    tags=["workspaces", "members"],
)
async def list_members(
    access: Annotated[WorkspaceAccess, Depends(get_workspace_access)],
    pagination: Annotated[PaginationParams, Depends()],
    repos: ReposDep,
) -> Page[WorkspaceMemberResponse]:
    members = await repos.workspaces.list_members(access.workspace_id)
    start = pagination.offset
    end = start + pagination.limit
    page = members[start:end]

    items: list[WorkspaceMemberResponse] = []
    for m in page:
        user = await repos.users.get_by_id(m.user_id)
        items.append(WorkspaceMemberResponse(
            id=m.id,
            workspace_id=m.workspace_id,
            user_id=m.user_id,
            email=user.email if user else None,  # type: ignore[arg-type]
            full_name=user.full_name if user else None,
            role=WorkspaceRole(m.role),
            created_at=m.created_at,
        ))

    return Page(items=items, pagination=pagination.to_meta(len(members)))


@router.post(
    "/{workspace_id}/members",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a member by email",
    responses=_ERRORS,
    tags=["workspaces", "members"],
)
async def add_member(
    body: WorkspaceMemberCreate,
    access: Annotated[
        WorkspaceAccess,
        Depends(require_roles(WorkspaceRole.OWNER, WorkspaceRole.ADMIN)),
    ],
    repos: ReposDep,
) -> WorkspaceMemberResponse:
    try:
        member = await ws_uc.invite_member(
            workspace_id=access.workspace_id,
            email=str(body.email),
            role=body.role,  # type: ignore[arg-type]
            workspaces=repos.workspaces,
            users=repos.users,
        )
    except DomainError as exc:
        raise _domain_error_to_http(exc) from exc
    user = await repos.users.get_by_id(member.user_id)
    return WorkspaceMemberResponse(
        id=member.id,
        workspace_id=member.workspace_id,
        user_id=member.user_id,
        email=user.email if user else None,  # type: ignore[arg-type]
        full_name=user.full_name if user else None,
        role=WorkspaceRole(member.role),
        created_at=member.created_at,
    )


@router.patch(
    "/{workspace_id}/members/{user_id}",
    response_model=WorkspaceMemberResponse,
    summary="Update member role",
    responses=_ERRORS,
    tags=["workspaces", "members"],
)
async def update_member(
    user_id: UUID,
    body: WorkspaceMemberUpdate,
    access: Annotated[
        WorkspaceAccess,
        Depends(require_roles(WorkspaceRole.OWNER, WorkspaceRole.ADMIN)),
    ],
    repos: ReposDep,
) -> WorkspaceMemberResponse:
    try:
        member = await ws_uc.update_member_role(
            workspace_id=access.workspace_id,
            user_id=user_id,
            role=body.role,  # type: ignore[arg-type]
            workspaces=repos.workspaces,
        )
    except DomainError as exc:
        raise _domain_error_to_http(exc) from exc
    user = await repos.users.get_by_id(member.user_id)
    return WorkspaceMemberResponse(
        id=member.id,
        workspace_id=member.workspace_id,
        user_id=member.user_id,
        email=user.email if user else None,  # type: ignore[arg-type]
        full_name=user.full_name if user else None,
        role=WorkspaceRole(member.role),
        created_at=member.created_at,
    )


@router.delete(
    "/{workspace_id}/members/{user_id}",
    response_model=MessageResponse,
    summary="Remove a member",
    responses=_ERRORS,
    tags=["workspaces", "members"],
)
async def remove_member(
    user_id: UUID,
    access: Annotated[
        WorkspaceAccess,
        Depends(require_roles(WorkspaceRole.OWNER, WorkspaceRole.ADMIN)),
    ],
    repos: ReposDep,
) -> MessageResponse:
    try:
        await ws_uc.remove_member(
            workspace_id=access.workspace_id,
            user_id=user_id,
            workspaces=repos.workspaces,
        )
    except DomainError as exc:
        raise _domain_error_to_http(exc) from exc
    return MessageResponse(message="Member removed")
