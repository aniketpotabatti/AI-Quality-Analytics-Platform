"""SQLAlchemy repository implementations."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from has_api.application.ports.repositories import (
    DatasetRepository,
    EvaluationResultRepository,
    EvaluationRunRepository,
    TestCaseRepository,
    UserRepository,
    WorkspaceRepository,
)
from has_api.domain.entities import (
    Dataset,
    EvaluationResult,
    EvaluationRun,
    MetricScore,
    TestCase,
    User,
    Workspace,
    WorkspaceMember,
)
from has_api.infrastructure.database.mappers.datasets import (
    dataset_to_domain,
    dataset_to_orm,
    test_case_to_domain,
    test_case_to_orm,
)
from has_api.infrastructure.database.mappers.evaluations import (
    evaluation_result_to_domain,
    evaluation_result_to_orm,
    evaluation_run_to_domain,
    evaluation_run_to_orm,
    metric_score_to_domain,
    metric_score_to_orm,
)
from has_api.infrastructure.database.mappers.identity import (
    user_to_domain,
    user_to_orm,
    workspace_member_to_domain,
    workspace_member_to_orm,
    workspace_to_domain,
    workspace_to_orm,
)
from has_api.infrastructure.database.models.datasets import DatasetModel, TestCaseModel
from has_api.infrastructure.database.models.evaluations import (
    EvaluationResultModel,
    EvaluationRunModel,
    MetricScoreModel,
)
from has_api.infrastructure.database.models.identity import (
    UserModel,
    WorkspaceMemberModel,
    WorkspaceModel,
)

__all__ = [
    "SqlAlchemyDatasetRepository",
    "SqlAlchemyEvaluationResultRepository",
    "SqlAlchemyEvaluationRunRepository",
    "SqlAlchemyTestCaseRepository",
    "SqlAlchemyUserRepository",
    "SqlAlchemyWorkspaceRepository",
]


# ── Identity ─────────────────────────────────────────────────────────────────


class SqlAlchemyWorkspaceRepository(WorkspaceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, workspace_id: UUID) -> Workspace | None:
        model = await self._session.get(WorkspaceModel, workspace_id)
        return workspace_to_domain(model) if model else None

    async def get_by_slug(self, slug: str) -> Workspace | None:
        result = await self._session.execute(
            select(WorkspaceModel).where(WorkspaceModel.slug == slug)
        )
        model = result.scalar_one_or_none()
        return workspace_to_domain(model) if model else None

    async def save(self, workspace: Workspace) -> Workspace:
        model = await self._session.get(WorkspaceModel, workspace.id)
        model = workspace_to_orm(workspace, model)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return workspace_to_domain(model)

    async def save_member(self, member: WorkspaceMember) -> WorkspaceMember:
        existing = await self._session.execute(
            select(WorkspaceMemberModel).where(
                WorkspaceMemberModel.workspace_id == member.workspace_id,
                WorkspaceMemberModel.user_id == member.user_id,
            )
        )
        model = existing.scalar_one_or_none()
        model = workspace_member_to_orm(member, model)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return workspace_member_to_domain(model)

    async def get_member(
        self, workspace_id: UUID, user_id: UUID
    ) -> WorkspaceMember | None:
        result = await self._session.execute(
            select(WorkspaceMemberModel).where(
                WorkspaceMemberModel.workspace_id == workspace_id,
                WorkspaceMemberModel.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        return workspace_member_to_domain(model) if model else None

    async def list_members(self, workspace_id: UUID) -> list[WorkspaceMember]:
        result = await self._session.execute(
            select(WorkspaceMemberModel)
            .where(WorkspaceMemberModel.workspace_id == workspace_id)
            .order_by(WorkspaceMemberModel.created_at)
        )
        return [workspace_member_to_domain(m) for m in result.scalars().all()]

    async def list_memberships_for_user(self, user_id: UUID) -> list[WorkspaceMember]:
        result = await self._session.execute(
            select(WorkspaceMemberModel)
            .where(WorkspaceMemberModel.user_id == user_id)
            .order_by(WorkspaceMemberModel.created_at)
        )
        return [workspace_member_to_domain(m) for m in result.scalars().all()]

    async def delete_member(self, workspace_id: UUID, user_id: UUID) -> None:
        result = await self._session.execute(
            select(WorkspaceMemberModel).where(
                WorkspaceMemberModel.workspace_id == workspace_id,
                WorkspaceMemberModel.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        model = await self._session.get(UserModel, user_id)
        return user_to_domain(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(UserModel).where(UserModel.email == email))
        model = result.scalar_one_or_none()
        return user_to_domain(model) if model else None

    async def save(self, user: User) -> User:
        model = await self._session.get(UserModel, user.id)
        model = user_to_orm(user, model)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return user_to_domain(model)


# ── Datasets ──────────────────────────────────────────────────────────────────


class SqlAlchemyDatasetRepository(DatasetRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, workspace_id: UUID, dataset_id: UUID) -> Dataset | None:
        result = await self._session.execute(
            select(DatasetModel).where(
                DatasetModel.id == dataset_id,
                DatasetModel.workspace_id == workspace_id,
            )
        )
        model = result.scalar_one_or_none()
        return dataset_to_domain(model) if model else None

    async def list_by_workspace(
        self,
        workspace_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Dataset]:
        result = await self._session.execute(
            select(DatasetModel)
            .where(DatasetModel.workspace_id == workspace_id)
            .order_by(DatasetModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [dataset_to_domain(model) for model in result.scalars().all()]

    async def count_by_workspace(self, workspace_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(DatasetModel).where(
                DatasetModel.workspace_id == workspace_id
            )
        )
        return int(result.scalar_one())

    async def save(self, dataset: Dataset) -> Dataset:
        model = await self._session.get(DatasetModel, dataset.id)
        model = dataset_to_orm(dataset, model)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return dataset_to_domain(model)

    async def delete(self, workspace_id: UUID, dataset_id: UUID) -> None:
        result = await self._session.execute(
            select(DatasetModel).where(
                DatasetModel.id == dataset_id,
                DatasetModel.workspace_id == workspace_id,
            )
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)


class SqlAlchemyTestCaseRepository(TestCaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, dataset_id: UUID, test_case_id: UUID) -> TestCase | None:
        result = await self._session.execute(
            select(TestCaseModel).where(
                TestCaseModel.id == test_case_id,
                TestCaseModel.dataset_id == dataset_id,
            )
        )
        model = result.scalar_one_or_none()
        return test_case_to_domain(model) if model else None

    async def list_by_dataset(
        self,
        dataset_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TestCase]:
        result = await self._session.execute(
            select(TestCaseModel)
            .where(TestCaseModel.dataset_id == dataset_id)
            .order_by(TestCaseModel.sort_order, TestCaseModel.created_at)
            .limit(limit)
            .offset(offset)
        )
        return [test_case_to_domain(model) for model in result.scalars().all()]

    async def count_by_dataset(self, dataset_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(TestCaseModel).where(
                TestCaseModel.dataset_id == dataset_id
            )
        )
        return int(result.scalar_one())

    async def save(self, test_case: TestCase) -> TestCase:
        model = await self._session.get(TestCaseModel, test_case.id)
        model = test_case_to_orm(test_case, model)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return test_case_to_domain(model)

    async def save_many(self, test_cases: list[TestCase]) -> list[TestCase]:
        saved: list[TestCase] = []
        for test_case in test_cases:
            saved.append(await self.save(test_case))
        return saved

    async def delete(self, dataset_id: UUID, test_case_id: UUID) -> None:
        result = await self._session.execute(
            select(TestCaseModel).where(
                TestCaseModel.id == test_case_id,
                TestCaseModel.dataset_id == dataset_id,
            )
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)


# ── Evaluations ───────────────────────────────────────────────────────────────


class SqlAlchemyEvaluationRunRepository(EvaluationRunRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, workspace_id: UUID, run_id: UUID) -> EvaluationRun | None:
        result = await self._session.execute(
            select(EvaluationRunModel).where(
                EvaluationRunModel.id == run_id,
                EvaluationRunModel.workspace_id == workspace_id,
            )
        )
        model = result.scalar_one_or_none()
        return evaluation_run_to_domain(model) if model else None

    async def list_by_workspace(
        self,
        workspace_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
        status_filter: str | None = None,
        dataset_id: UUID | None = None,
    ) -> list[EvaluationRun]:
        q = select(EvaluationRunModel).where(
            EvaluationRunModel.workspace_id == workspace_id
        )
        if status_filter:
            q = q.where(EvaluationRunModel.status == status_filter)
        if dataset_id:
            q = q.where(EvaluationRunModel.dataset_id == dataset_id)
        q = q.order_by(EvaluationRunModel.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(q)
        return [evaluation_run_to_domain(m) for m in result.scalars().all()]

    async def count_by_workspace(
        self,
        workspace_id: UUID,
        *,
        status_filter: str | None = None,
        dataset_id: UUID | None = None,
    ) -> int:
        q = select(func.count()).select_from(EvaluationRunModel).where(
            EvaluationRunModel.workspace_id == workspace_id
        )
        if status_filter:
            q = q.where(EvaluationRunModel.status == status_filter)
        if dataset_id:
            q = q.where(EvaluationRunModel.dataset_id == dataset_id)
        result = await self._session.execute(q)
        return int(result.scalar_one())

    async def save(self, run: EvaluationRun) -> EvaluationRun:
        model = await self._session.get(EvaluationRunModel, run.id)
        model = evaluation_run_to_orm(run, model)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return evaluation_run_to_domain(model)


class SqlAlchemyEvaluationResultRepository(EvaluationResultRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, run_id: UUID, result_id: UUID) -> EvaluationResult | None:
        result = await self._session.execute(
            select(EvaluationResultModel).where(
                EvaluationResultModel.id == result_id,
                EvaluationResultModel.run_id == run_id,
            )
        )
        model = result.scalar_one_or_none()
        return evaluation_result_to_domain(model) if model else None

    async def list_by_run(
        self,
        run_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EvaluationResult]:
        result = await self._session.execute(
            select(EvaluationResultModel)
            .where(EvaluationResultModel.run_id == run_id)
            .order_by(EvaluationResultModel.created_at)
            .limit(limit)
            .offset(offset)
        )
        return [evaluation_result_to_domain(m) for m in result.scalars().all()]

    async def count_by_run(self, run_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(EvaluationResultModel).where(
                EvaluationResultModel.run_id == run_id
            )
        )
        return int(result.scalar_one())

    async def save(self, result_obj: EvaluationResult) -> EvaluationResult:
        model = await self._session.get(EvaluationResultModel, result_obj.id)
        model = evaluation_result_to_orm(result_obj, model)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return evaluation_result_to_domain(model)

    async def save_many(self, results: list[EvaluationResult]) -> list[EvaluationResult]:
        return [await self.save(r) for r in results]

    async def list_scores_for_result(self, result_id: UUID) -> list[MetricScore]:
        result = await self._session.execute(
            select(MetricScoreModel)
            .where(MetricScoreModel.result_id == result_id)
            .order_by(MetricScoreModel.created_at)
        )
        return [metric_score_to_domain(m) for m in result.scalars().all()]

    async def save_score(self, score: MetricScore) -> MetricScore:
        model = await self._session.get(MetricScoreModel, score.id)
        model = metric_score_to_orm(score, model)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return metric_score_to_domain(model)
