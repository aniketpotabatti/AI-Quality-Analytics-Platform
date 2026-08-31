"""Workspace use cases: create, list, manage members."""

from __future__ import annotations

import re
from uuid import UUID

from has_api.application.ports.repositories import UserRepository, WorkspaceRepository
from has_api.domain.entities import Workspace, WorkspaceMember
from has_api.domain.exceptions import ConflictError, NotFoundError
from has_api.domain.value_objects import WorkspaceRole


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:100] or "workspace"


async def create_workspace(
    *,
    name: str,
    slug: str,
    created_by_id: UUID,
    workspaces: WorkspaceRepository,
) -> Workspace:
    """Create a new workspace and add the creator as owner."""
    if await workspaces.get_by_slug(slug) is not None:
        raise ConflictError("slug_taken", f"Workspace slug already taken: {slug}")

    workspace = Workspace(name=name, slug=slug)
    workspace = await workspaces.save(workspace)

    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=created_by_id,
        role=WorkspaceRole.OWNER,
    )
    await workspaces.save_member(member)
    return workspace


async def update_workspace(
    *,
    workspace_id: UUID,
    name: str | None,
    workspaces: WorkspaceRepository,
) -> Workspace:
    workspace = await workspaces.get_by_id(workspace_id)
    if workspace is None:
        raise NotFoundError("workspace", workspace_id)
    if name is not None:
        workspace.name = name
    return await workspaces.save(workspace)


async def invite_member(
    *,
    workspace_id: UUID,
    email: str,
    role: WorkspaceRole,
    workspaces: WorkspaceRepository,
    users: UserRepository,
) -> WorkspaceMember:
    """Add an existing user to a workspace."""
    user = await users.get_by_email(email)
    if user is None:
        raise NotFoundError("user", email)

    existing = await workspaces.get_member(workspace_id, user.id)
    if existing is not None:
        raise ConflictError("already_member", f"User {email} is already a member")

    member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=user.id,
        role=role,
    )
    return await workspaces.save_member(member)


async def update_member_role(
    *,
    workspace_id: UUID,
    user_id: UUID,
    role: WorkspaceRole,
    workspaces: WorkspaceRepository,
) -> WorkspaceMember:
    member = await workspaces.get_member(workspace_id, user_id)
    if member is None:
        raise NotFoundError("workspace_member", user_id)
    if member.role == WorkspaceRole.OWNER:
        from has_api.domain.exceptions import AuthorizationError
        raise AuthorizationError("Cannot change owner's role directly")
    member.role = role
    return await workspaces.save_member(member)


async def remove_member(
    *,
    workspace_id: UUID,
    user_id: UUID,
    workspaces: WorkspaceRepository,
) -> None:
    member = await workspaces.get_member(workspace_id, user_id)
    if member is None:
        raise NotFoundError("workspace_member", user_id)
    if member.role == WorkspaceRole.OWNER:
        from has_api.domain.exceptions import AuthorizationError
        raise AuthorizationError("Cannot remove workspace owner")
    await workspaces.delete_member(workspace_id, user_id)
