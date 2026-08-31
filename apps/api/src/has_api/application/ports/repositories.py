"""Repository port interfaces (implemented in infrastructure layer)."""

from abc import ABC, abstractmethod
from uuid import UUID

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


class WorkspaceRepository(ABC):
    @abstractmethod
    async def get_by_id(self, workspace_id: UUID) -> Workspace | None: ...

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Workspace | None: ...

    @abstractmethod
    async def save(self, workspace: Workspace) -> Workspace: ...

    @abstractmethod
    async def save_member(self, member: WorkspaceMember) -> WorkspaceMember: ...

    @abstractmethod
    async def get_member(
        self, workspace_id: UUID, user_id: UUID
    ) -> WorkspaceMember | None: ...

    @abstractmethod
    async def list_members(self, workspace_id: UUID) -> list[WorkspaceMember]: ...

    @abstractmethod
    async def list_memberships_for_user(self, user_id: UUID) -> list[WorkspaceMember]: ...

    @abstractmethod
    async def delete_member(self, workspace_id: UUID, user_id: UUID) -> None: ...


class UserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def save(self, user: User) -> User: ...


class DatasetRepository(ABC):
    @abstractmethod
    async def get_by_id(self, workspace_id: UUID, dataset_id: UUID) -> Dataset | None: ...

    @abstractmethod
    async def list_by_workspace(
        self,
        workspace_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Dataset]: ...

    @abstractmethod
    async def count_by_workspace(self, workspace_id: UUID) -> int: ...

    @abstractmethod
    async def save(self, dataset: Dataset) -> Dataset: ...

    @abstractmethod
    async def delete(self, workspace_id: UUID, dataset_id: UUID) -> None: ...


class TestCaseRepository(ABC):
    @abstractmethod
    async def get_by_id(self, dataset_id: UUID, test_case_id: UUID) -> TestCase | None: ...

    @abstractmethod
    async def list_by_dataset(
        self,
        dataset_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TestCase]: ...

    @abstractmethod
    async def count_by_dataset(self, dataset_id: UUID) -> int: ...

    @abstractmethod
    async def save(self, test_case: TestCase) -> TestCase: ...

    @abstractmethod
    async def save_many(self, test_cases: list[TestCase]) -> list[TestCase]: ...

    @abstractmethod
    async def delete(self, dataset_id: UUID, test_case_id: UUID) -> None: ...


class EvaluationRunRepository(ABC):
    @abstractmethod
    async def get_by_id(self, workspace_id: UUID, run_id: UUID) -> EvaluationRun | None: ...

    @abstractmethod
    async def list_by_workspace(
        self,
        workspace_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
        status_filter: str | None = None,
        dataset_id: UUID | None = None,
    ) -> list[EvaluationRun]: ...

    @abstractmethod
    async def count_by_workspace(
        self,
        workspace_id: UUID,
        *,
        status_filter: str | None = None,
        dataset_id: UUID | None = None,
    ) -> int: ...

    @abstractmethod
    async def save(self, run: EvaluationRun) -> EvaluationRun: ...


class EvaluationResultRepository(ABC):
    @abstractmethod
    async def get_by_id(self, run_id: UUID, result_id: UUID) -> EvaluationResult | None: ...

    @abstractmethod
    async def list_by_run(
        self,
        run_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EvaluationResult]: ...

    @abstractmethod
    async def count_by_run(self, run_id: UUID) -> int: ...

    @abstractmethod
    async def save(self, result: EvaluationResult) -> EvaluationResult: ...

    @abstractmethod
    async def save_many(self, results: list[EvaluationResult]) -> list[EvaluationResult]: ...

    @abstractmethod
    async def list_scores_for_result(self, result_id: UUID) -> list[MetricScore]: ...

    @abstractmethod
    async def save_score(self, score: MetricScore) -> MetricScore: ...
