"""Workspace API key management — fully implemented."""

import secrets
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from has_api.api.dependencies.auth import WorkspaceAccess, require_roles
from has_api.api.deps import PaginationParams
from has_api.api.schemas.api_keys import (
    ApiKeyCreate,
    ApiKeyCreatedResponse,
    ApiKeyResponse,
)
from has_api.api.schemas.common import MessageResponse, Page, ProblemDetail
from has_api.api.schemas.enums import WorkspaceRole
from has_api.infrastructure.auth.password import hash_password
from has_api.infrastructure.database.models.identity import ApiKeyModel
from has_api.infrastructure.database.session import get_db_session

router = APIRouter(
    prefix="/workspaces/{workspace_id}/api-keys",
    tags=["api-keys"],
)

_ERRORS = {
    401: {"model": ProblemDetail},
    403: {"model": ProblemDetail},
    404: {"model": ProblemDetail},
}

_ADMIN = Depends(require_roles(WorkspaceRole.OWNER, WorkspaceRole.ADMIN))


@router.get(
    "",
    response_model=Page[ApiKeyResponse],
    summary="List API keys for a workspace",
    responses=_ERRORS,
)
async def list_api_keys(
    access: Annotated[WorkspaceAccess, _ADMIN],
    pagination: Annotated[PaginationParams, Depends()],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Page[ApiKeyResponse]:
    result = await session.execute(
        select(ApiKeyModel)
        .where(ApiKeyModel.workspace_id == access.workspace_id, ApiKeyModel.is_active.is_(True))
        .order_by(ApiKeyModel.created_at.desc())
        .limit(pagination.limit)
        .offset(pagination.offset)
    )
    keys = result.scalars().all()
    count_result = await session.execute(
        select(func.count()).select_from(ApiKeyModel).where(
            ApiKeyModel.workspace_id == access.workspace_id,
            ApiKeyModel.is_active.is_(True),
        )
    )
    total = int(count_result.scalar_one())

    items = [
        ApiKeyResponse(
            id=k.id,
            workspace_id=k.workspace_id,
            name=k.name,
            key_prefix=k.key_prefix,
            is_active=k.is_active,
            last_used_at=k.last_used_at,
            expires_at=k.expires_at,
            created_by_id=k.created_by_id,
            created_at=k.created_at,
        )
        for k in keys
    ]
    return Page(items=items, pagination=pagination.to_meta(total))


@router.post(
    "",
    response_model=ApiKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an API key (raw secret returned once)",
    responses=_ERRORS,
)
async def create_api_key(
    body: ApiKeyCreate,
    access: Annotated[WorkspaceAccess, _ADMIN],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiKeyCreatedResponse:
    if access.principal.user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    raw_key = "has_" + secrets.token_urlsafe(32)
    prefix = raw_key[:8]
    key_hash = hash_password(raw_key)
    model = ApiKeyModel(
        workspace_id=access.workspace_id,
        name=body.name,
        key_hash=key_hash,
        key_prefix=prefix,
        created_by_id=access.principal.user_id,
        is_active=True,
        expires_at=body.expires_at,
        created_at=datetime.now(UTC),
    )
    session.add(model)
    await session.flush()
    await session.refresh(model)

    return ApiKeyCreatedResponse(
        id=model.id,
        workspace_id=model.workspace_id,
        name=model.name,
        key_prefix=model.key_prefix,
        is_active=model.is_active,
        last_used_at=model.last_used_at,
        expires_at=model.expires_at,
        created_by_id=model.created_by_id,
        created_at=model.created_at,
        raw_key=raw_key,
    )


@router.delete(
    "/{key_id}",
    response_model=MessageResponse,
    summary="Revoke an API key",
    responses=_ERRORS,
)
async def revoke_api_key(
    key_id: UUID,
    access: Annotated[WorkspaceAccess, _ADMIN],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MessageResponse:
    result = await session.execute(
        select(ApiKeyModel).where(
            ApiKeyModel.id == key_id,
            ApiKeyModel.workspace_id == access.workspace_id,
        )
    )
    key = result.scalar_one_or_none()
    if key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"type": "about:blank", "title": "Not Found", "status": 404,
                    "detail": f"API key not found: {key_id}", "code": "not_found"},
        )
    key.is_active = False
    session.add(key)
    return MessageResponse(message="API key revoked")
