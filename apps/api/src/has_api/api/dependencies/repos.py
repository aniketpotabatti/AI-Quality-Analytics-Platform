"""FastAPI dependency: database repository container."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from has_api.infrastructure.database.repository_factory import RepositoryContainer
from has_api.infrastructure.database.session import get_db_session


async def get_repos(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RepositoryContainer:
    """Provide a per-request RepositoryContainer bound to the current session."""
    return RepositoryContainer(session)


ReposDep = Annotated[RepositoryContainer, Depends(get_repos)]
