"""Maps model registry ORM models to domain entities."""

from has_api.domain.entities import ModelConfig
from has_api.domain.value_objects import LlmProvider
from has_api.infrastructure.database.models.model_registry import ModelConfigModel


def model_config_to_domain(model: ModelConfigModel) -> ModelConfig:
    return ModelConfig(
        id=model.id,
        workspace_id=model.workspace_id,
        name=model.name,
        provider=LlmProvider(model.provider),
        model_id=model.model_id,
        config=model.config or {},
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def model_config_to_orm(
    domain: ModelConfig,
    model: ModelConfigModel | None = None,
) -> ModelConfigModel:
    if model is None:
        model = ModelConfigModel(id=domain.id)
    model.workspace_id = domain.workspace_id
    model.name = domain.name
    model.provider = domain.provider.value
    model.model_id = domain.model_id
    model.config = domain.config
    model.created_at = domain.created_at
    model.updated_at = domain.updated_at
    return model
