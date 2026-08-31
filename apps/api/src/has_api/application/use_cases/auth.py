"""Auth use cases: register, login, refresh, get-me."""

from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import UUID

from has_api.application.ports.repositories import UserRepository, WorkspaceRepository
from has_api.domain.entities import User, Workspace, WorkspaceMember
from has_api.domain.exceptions import (
    ConflictError,
    NotFoundError,
    UnauthorizedError,
)
from has_api.domain.value_objects import WorkspaceRole
from has_api.infrastructure.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from has_api.infrastructure.auth.password import hash_password, verify_password


# ── helpers ─────────────────────────────────────────────────────────────────


def _slugify(name: str) -> str:
    """Convert workspace name to a URL-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:100] or "workspace"


# ── DTOs ─────────────────────────────────────────────────────────────────────


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int  # seconds


@dataclass
class MembershipInfo:
    workspace_id: UUID
    workspace_name: str
    workspace_slug: str
    role: WorkspaceRole


@dataclass
class MeResult:
    user: User
    memberships: list[MembershipInfo]


# ── use cases ─────────────────────────────────────────────────────────────────


async def register(
    *,
    email: str,
    password: str,
    full_name: str,
    workspace_name: str,
    users: UserRepository,
    workspaces: WorkspaceRepository,
) -> tuple[User, Workspace, TokenPair]:
    """Create a new user + personal workspace, return tokens."""
    existing = await users.get_by_email(email)
    if existing is not None:
        raise ConflictError("email_taken", f"Email already registered: {email}")

    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
    )
    user = await users.save(user)

    # Derive unique slug
    base_slug = _slugify(workspace_name)
    slug = base_slug
    attempt = 1
    while await workspaces.get_by_slug(slug) is not None:
        slug = f"{base_slug}-{attempt}"
        attempt += 1

    workspace = Workspace(name=workspace_name, slug=slug)
    workspace = await workspaces.save(workspace)

    # Workspace member record — owner
    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=user.id,
        role=WorkspaceRole.OWNER,
    )
    await workspaces.save_member(member)

    from has_api.config import get_settings

    settings = get_settings()
    pair = TokenPair(
        access_token=create_access_token(user.id, workspace.id),
        refresh_token=create_refresh_token(user.id),
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )
    return user, workspace, pair


async def login(
    *,
    email: str,
    password: str,
    users: UserRepository,
    workspaces: WorkspaceRepository,
) -> tuple[User, TokenPair]:
    """Verify credentials and issue tokens."""
    user = await users.get_by_email(email)
    if user is None or not verify_password(password, user.hashed_password):
        raise UnauthorizedError("invalid_credentials", "Invalid email or password")
    if not user.is_active:
        raise UnauthorizedError("inactive_user", "User account is disabled")

    # Find first workspace membership to embed in access token
    memberships = await workspaces.list_memberships_for_user(user.id)
    default_ws_id = memberships[0].workspace_id if memberships else None

    from has_api.config import get_settings

    settings = get_settings()
    pair = TokenPair(
        access_token=create_access_token(user.id, default_ws_id),
        refresh_token=create_refresh_token(user.id),
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )
    return user, pair


async def refresh_tokens(
    *,
    refresh_token: str,
    users: UserRepository,
    workspaces: WorkspaceRepository,
) -> TokenPair:
    """Validate a refresh token and issue a new token pair."""
    payload = decode_token(refresh_token)
    if payload is None or payload.type != "refresh":
        raise UnauthorizedError("invalid_token", "Invalid or expired refresh token")

    user_id = UUID(payload.sub)
    user = await users.get_by_id(user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("invalid_token", "User not found or inactive")

    memberships = await workspaces.list_memberships_for_user(user.id)
    default_ws_id = memberships[0].workspace_id if memberships else None

    from has_api.config import get_settings

    settings = get_settings()
    return TokenPair(
        access_token=create_access_token(user.id, default_ws_id),
        refresh_token=create_refresh_token(user.id),
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


async def get_me(
    *,
    user_id: UUID,
    users: UserRepository,
    workspaces: WorkspaceRepository,
) -> MeResult:
    """Return current user and their workspace memberships."""
    user = await users.get_by_id(user_id)
    if user is None:
        raise NotFoundError("user_not_found", "User not found")

    memberships = await workspaces.list_memberships_for_user(user_id)
    result_memberships: list[MembershipInfo] = []
    for m in memberships:
        ws = await workspaces.get_by_id(m.workspace_id)
        if ws:
            result_memberships.append(
                MembershipInfo(
                    workspace_id=ws.id,
                    workspace_name=ws.name,
                    workspace_slug=ws.slug,
                    role=m.role,
                )
            )

    return MeResult(user=user, memberships=result_memberships)
