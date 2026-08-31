"""Maps identity ORM models to domain entities."""

from has_api.domain.entities import ApiKey, User, Workspace, WorkspaceMember
from has_api.domain.value_objects import WorkspaceRole
from has_api.infrastructure.database.models.identity import (
    ApiKeyModel,
    UserModel,
    WorkspaceMemberModel,
    WorkspaceModel,
)


def workspace_to_domain(model: WorkspaceModel) -> Workspace:
    return Workspace(
        id=model.id,
        name=model.name,
        slug=model.slug,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def workspace_to_orm(domain: Workspace, model: WorkspaceModel | None = None) -> WorkspaceModel:
    if model is None:
        model = WorkspaceModel(id=domain.id)
    model.name = domain.name
    model.slug = domain.slug
    model.created_at = domain.created_at
    model.updated_at = domain.updated_at
    return model


def user_to_domain(model: UserModel) -> User:
    return User(
        id=model.id,
        email=model.email,
        hashed_password=model.hashed_password,
        full_name=model.full_name,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def user_to_orm(domain: User, model: UserModel | None = None) -> UserModel:
    if model is None:
        model = UserModel(id=domain.id)
    model.email = domain.email
    model.hashed_password = domain.hashed_password
    model.full_name = domain.full_name
    model.is_active = domain.is_active
    model.created_at = domain.created_at
    model.updated_at = domain.updated_at
    return model


def workspace_member_to_domain(model: WorkspaceMemberModel) -> WorkspaceMember:
    return WorkspaceMember(
        id=model.id,
        workspace_id=model.workspace_id,
        user_id=model.user_id,
        role=WorkspaceRole(model.role),
        created_at=model.created_at,
    )


def workspace_member_to_orm(
    domain: WorkspaceMember,
    model: WorkspaceMemberModel | None = None,
) -> WorkspaceMemberModel:
    if model is None:
        model = WorkspaceMemberModel(id=domain.id)
    model.workspace_id = domain.workspace_id
    model.user_id = domain.user_id
    model.role = domain.role.value
    model.created_at = domain.created_at
    return model


def api_key_to_domain(model: ApiKeyModel) -> ApiKey:
    if model.created_by_id is None:
        msg = "ApiKeyModel.created_by_id is required for domain mapping"
        raise ValueError(msg)
    return ApiKey(
        id=model.id,
        workspace_id=model.workspace_id,
        name=model.name,
        key_hash=model.key_hash,
        key_prefix=model.key_prefix,
        created_by_id=model.created_by_id,
        is_active=model.is_active,
        last_used_at=model.last_used_at,
        expires_at=model.expires_at,
        created_at=model.created_at,
    )


def api_key_to_orm(domain: ApiKey, model: ApiKeyModel | None = None) -> ApiKeyModel:
    if model is None:
        model = ApiKeyModel(id=domain.id)
    model.workspace_id = domain.workspace_id
    model.name = domain.name
    model.key_hash = domain.key_hash
    model.key_prefix = domain.key_prefix
    model.created_by_id = domain.created_by_id
    model.is_active = domain.is_active
    model.last_used_at = domain.last_used_at
    model.expires_at = domain.expires_at
    model.created_at = domain.created_at
    return model
