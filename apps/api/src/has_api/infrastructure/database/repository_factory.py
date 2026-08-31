"""Factory for repository instances bound to a database session."""

from sqlalchemy.ext.asyncio import AsyncSession

from has_api.application.ports.repositories import (
    DatasetRepository,
    EvaluationResultRepository,
    EvaluationRunRepository,
    TestCaseRepository,
    UserRepository,
    WorkspaceRepository,
)
from has_api.infrastructure.database.repositories import (
    SqlAlchemyDatasetRepository,
    SqlAlchemyEvaluationResultRepository,
    SqlAlchemyEvaluationRunRepository,
    SqlAlchemyTestCaseRepository,
    SqlAlchemyUserRepository,
    SqlAlchemyWorkspaceRepository,
)


class RepositoryContainer:
    """Provides repository instances for a single request/worker session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @property
    def workspaces(self) -> WorkspaceRepository:
        return SqlAlchemyWorkspaceRepository(self._session)

    @property
    def users(self) -> UserRepository:
        return SqlAlchemyUserRepository(self._session)

    @property
    def datasets(self) -> DatasetRepository:
        return SqlAlchemyDatasetRepository(self._session)

    @property
    def test_cases(self) -> TestCaseRepository:
        return SqlAlchemyTestCaseRepository(self._session)

    @property
    def evaluation_runs(self) -> EvaluationRunRepository:
        return SqlAlchemyEvaluationRunRepository(self._session)

    @property
    def evaluation_results(self) -> EvaluationResultRepository:
        return SqlAlchemyEvaluationResultRepository(self._session)
