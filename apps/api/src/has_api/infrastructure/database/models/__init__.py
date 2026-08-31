"""SQLAlchemy ORM models — import all models so Alembic discovers metadata."""

from has_api.infrastructure.database.models.datasets import DatasetModel, TestCaseModel
from has_api.infrastructure.database.models.evaluations import (
    EvaluationResultModel,
    EvaluationRunModel,
    MetricScoreModel,
)
from has_api.infrastructure.database.models.identity import (
    ApiKeyModel,
    UserModel,
    WorkspaceMemberModel,
    WorkspaceModel,
)
from has_api.infrastructure.database.models.model_registry import ModelConfigModel

__all__ = [
    "ApiKeyModel",
    "DatasetModel",
    "EvaluationResultModel",
    "EvaluationRunModel",
    "MetricScoreModel",
    "ModelConfigModel",
    "TestCaseModel",
    "UserModel",
    "WorkspaceMemberModel",
    "WorkspaceModel",
]
