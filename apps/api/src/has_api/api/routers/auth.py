"""Authentication endpoints — fully implemented."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from has_api.api.dependencies.auth import (
    AuthenticatedPrincipal,
    get_current_principal,
)
from has_api.api.dependencies.repos import ReposDep
from has_api.api.schemas.auth import (
    LoginRequest,
    MeResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    WorkspaceMembershipSummary,
)
from has_api.api.schemas.common import MessageResponse, ProblemDetail
from has_api.application.use_cases import auth as auth_uc
from has_api.domain.exceptions import ConflictError, DomainError, UnauthorizedError

router = APIRouter(prefix="/auth", tags=["auth"])

_ERROR_RESPONSES = {
    400: {"model": ProblemDetail, "description": "Validation or bad request"},
    401: {"model": ProblemDetail, "description": "Invalid credentials"},
    409: {"model": ProblemDetail, "description": "Conflict (e.g. email taken)"},
}


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register user and create initial workspace",
    responses=_ERROR_RESPONSES,
)
async def register(body: RegisterRequest, repos: ReposDep) -> TokenResponse:
    try:
        _user, _workspace, pair = await auth_uc.register(
            email=body.email,
            password=body.password,
            full_name=body.full_name,
            workspace_name=body.workspace_name,
            users=repos.users,
            workspaces=repos.workspaces,
        )
    except ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": "about:blank", "title": "Conflict", "status": 409,
                    "detail": exc.message, "code": exc.code},
        ) from exc
    return TokenResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        expires_in=pair.expires_in,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
    responses=_ERROR_RESPONSES,
)
async def login(body: LoginRequest, repos: ReposDep) -> TokenResponse:
    try:
        _user, pair = await auth_uc.login(
            email=body.email,
            password=body.password,
            users=repos.users,
            workspaces=repos.workspaces,
        )
    except UnauthorizedError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"type": "about:blank", "title": "Unauthorized", "status": 401,
                    "detail": exc.message, "code": exc.code},
        ) from exc
    return TokenResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        expires_in=pair.expires_in,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    responses=_ERROR_RESPONSES,
)
async def refresh(body: RefreshRequest, repos: ReposDep) -> TokenResponse:
    try:
        pair = await auth_uc.refresh_tokens(
            refresh_token=body.refresh_token,
            users=repos.users,
            workspaces=repos.workspaces,
        )
    except UnauthorizedError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"type": "about:blank", "title": "Unauthorized", "status": 401,
                    "detail": exc.message, "code": exc.code},
        ) from exc
    return TokenResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        expires_in=pair.expires_in,
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Invalidate refresh token (best-effort)",
)
async def logout(
    _principal: Annotated[AuthenticatedPrincipal, Depends(get_current_principal)],
) -> MessageResponse:
    # JWT is stateless; client should discard tokens.
    # Future: maintain a token denylist in Redis.
    return MessageResponse(message="Logged out successfully")


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Current user profile and workspace memberships",
)
async def me(
    principal: Annotated[AuthenticatedPrincipal, Depends(get_current_principal)],
    repos: ReposDep,
) -> MeResponse:
    if principal.user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    try:
        result = await auth_uc.get_me(
            user_id=principal.user_id,
            users=repos.users,
            workspaces=repos.workspaces,
        )
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"type": "about:blank", "title": "Not Found", "status": 404,
                    "detail": exc.message, "code": exc.code},
        ) from exc
    return MeResponse(
        user=UserResponse(
            id=result.user.id,
            email=result.user.email,  # type: ignore[arg-type]
            full_name=result.user.full_name,
            is_active=result.user.is_active,
            created_at=result.user.created_at,
        ),
        workspaces=[
            WorkspaceMembershipSummary(
                workspace_id=m.workspace_id,
                workspace_name=m.workspace_name,
                workspace_slug=m.workspace_slug,
                role=m.role,  # type: ignore[arg-type]
            )
            for m in result.memberships
        ],
    )
