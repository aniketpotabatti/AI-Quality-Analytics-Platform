"""Schema integrity tests — no live database required."""

from datetime import UTC, datetime
from uuid import uuid4

from has_api.domain.entities import (
    ApiKey,
    Dataset,
    EvaluationResult,
    EvaluationRun,
    MetricScore,
    ModelConfig,
    User,
    Workspace,
    WorkspaceMember,
)
from has_api.domain.entities.datasets import TestCase as DomainTestCase
from has_api.domain.value_objects import (
    EvaluationResultStatus,
    EvaluationRunStatus,
    LlmProvider,
    MetricType,
    WorkspaceRole,
)
from has_api.infrastructure.database.base import Base
from has_api.infrastructure.database.mappers import (
    api_key_to_domain,
    api_key_to_orm,
    dataset_to_domain,
    dataset_to_orm,
    evaluation_result_to_domain,
    evaluation_result_to_orm,
    evaluation_run_to_domain,
    evaluation_run_to_orm,
    metric_score_to_domain,
    metric_score_to_orm,
    model_config_to_domain,
    model_config_to_orm,
    user_to_domain,
    user_to_orm,
    workspace_member_to_domain,
    workspace_member_to_orm,
    workspace_to_domain,
    workspace_to_orm,
)
# Alias so pytest does not collect functions named test_case_* as tests.
from has_api.infrastructure.database.mappers.datasets import (
    test_case_to_domain as map_test_case_to_domain,
    test_case_to_orm as map_test_case_to_orm,
)

# Register all ORM models on Base.metadata without importing TestCase* names.
import has_api.infrastructure.database.models  # noqa: F401

EXPECTED_TABLES = {
    "workspaces",
    "users",
    "workspace_members",
    "api_keys",
    "datasets",
    "test_cases",
    "model_configs",
    "evaluation_runs",
    "evaluation_results",
    "metric_scores",
}


def test_all_expected_tables_registered() -> None:
    registered = set(Base.metadata.tables.keys())
    assert EXPECTED_TABLES.issubset(registered), (
        f"Missing tables: {EXPECTED_TABLES - registered}"
    )


def test_workspace_scoped_tables_have_workspace_id() -> None:
    for table_name in (
        "api_keys",
        "datasets",
        "model_configs",
        "evaluation_runs",
        "workspace_members",
    ):
        table = Base.metadata.tables[table_name]
        assert "workspace_id" in table.c, f"{table_name} missing workspace_id"


def test_cascade_fks_from_workspace() -> None:
    """Workspace children should CASCADE on delete for tenant cleanup."""
    for table_name in ("datasets", "api_keys", "model_configs", "evaluation_runs"):
        table = Base.metadata.tables[table_name]
        workspace_fks = [
            fk for fk in table.foreign_keys if fk.column.table.name == "workspaces"
        ]
        assert workspace_fks, f"{table_name} missing FK to workspaces"
        assert all(fk.ondelete == "CASCADE" for fk in workspace_fks), (
            f"{table_name} workspace FK should CASCADE"
        )


def test_unique_constraints() -> None:
    members = Base.metadata.tables["workspace_members"]
    assert any(
        c.name == "uq_workspace_member" for c in members.constraints if hasattr(c, "name")
    )

    results = Base.metadata.tables["evaluation_results"]
    assert any(
        c.name == "uq_run_test_case" for c in results.constraints if hasattr(c, "name")
    )

    scores = Base.metadata.tables["metric_scores"]
    assert any(
        c.name == "uq_result_metric" for c in scores.constraints if hasattr(c, "name")
    )


def test_workspace_mapper_roundtrip() -> None:
    domain = Workspace(name="Acme", slug="acme")
    orm = workspace_to_orm(domain)
    restored = workspace_to_domain(orm)
    assert restored.id == domain.id
    assert restored.name == "Acme"
    assert restored.slug == "acme"


def test_user_mapper_roundtrip() -> None:
    domain = User(
        email="user@example.com",
        hashed_password="hashed",
        full_name="Test User",
    )
    restored = user_to_domain(user_to_orm(domain))
    assert restored.email == domain.email
    assert restored.full_name == domain.full_name
    assert restored.is_active is True


def test_workspace_member_mapper_roundtrip() -> None:
    domain = WorkspaceMember(
        workspace_id=uuid4(),
        user_id=uuid4(),
        role=WorkspaceRole.ADMIN,
    )
    restored = workspace_member_to_domain(workspace_member_to_orm(domain))
    assert restored.role == WorkspaceRole.ADMIN
    assert restored.workspace_id == domain.workspace_id


def test_api_key_mapper_roundtrip() -> None:
    domain = ApiKey(
        workspace_id=uuid4(),
        name="CI key",
        key_hash="hash",
        key_prefix="has_live_",
        created_by_id=uuid4(),
    )
    restored = api_key_to_domain(api_key_to_orm(domain))
    assert restored.name == "CI key"
    assert restored.key_prefix == "has_live_"
    assert restored.is_active is True


def test_dataset_and_test_case_mapper_roundtrip() -> None:
    dataset = Dataset(
        workspace_id=uuid4(),
        name="RAG eval set",
        description="v1",
        created_by_id=uuid4(),
    )
    restored_dataset = dataset_to_domain(dataset_to_orm(dataset))
    assert restored_dataset.name == "RAG eval set"

    case = DomainTestCase(
        dataset_id=dataset.id,
        prompt="What is X?",
        response="X is Y",
        context="Doc about Y",
        ground_truth="Y",
        metadata={"source": "unit-test"},
    )
    restored_case = map_test_case_to_domain(map_test_case_to_orm(case))
    assert restored_case.prompt == case.prompt
    assert restored_case.metadata == {"source": "unit-test"}


def test_evaluation_mappers_roundtrip() -> None:
    run = EvaluationRun(
        workspace_id=uuid4(),
        dataset_id=uuid4(),
        name="Run 1",
        status=EvaluationRunStatus.RUNNING,
        metrics_config={"metrics": ["faithfulness"]},
        created_by_id=uuid4(),
        total_cases=10,
        completed_cases=3,
    )
    restored_run = evaluation_run_to_domain(evaluation_run_to_orm(run))
    assert restored_run.status == EvaluationRunStatus.RUNNING
    assert restored_run.total_cases == 10

    result = EvaluationResult(
        run_id=run.id,
        test_case_id=uuid4(),
        status=EvaluationResultStatus.COMPLETED,
        overall_score=0.91,
    )
    restored_result = evaluation_result_to_domain(evaluation_result_to_orm(result))
    assert restored_result.overall_score == 0.91

    score = MetricScore(
        result_id=result.id,
        metric_type=MetricType.FAITHFULNESS,
        score=0.91,
        passed=True,
        rationale="Claims supported by context",
        metadata={"claims": 4},
        created_at=datetime.now(UTC),
    )
    restored_score = metric_score_to_domain(metric_score_to_orm(score))
    assert restored_score.metric_type == MetricType.FAITHFULNESS
    assert restored_score.passed is True
    assert restored_score.metadata == {"claims": 4}


def test_model_config_mapper_roundtrip() -> None:
    domain = ModelConfig(
        workspace_id=uuid4(),
        name="GPT-4o judge",
        provider=LlmProvider.OPENAI,
        model_id="gpt-4o",
        config={"temperature": 0},
    )
    restored = model_config_to_domain(model_config_to_orm(domain))
    assert restored.provider == LlmProvider.OPENAI
    assert restored.model_id == "gpt-4o"
    assert restored.config == {"temperature": 0}
