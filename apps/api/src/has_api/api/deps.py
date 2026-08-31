"""Shared FastAPI dependency helpers (pagination, stubs)."""

from typing import Annotated

from fastapi import HTTPException, Query, status

from has_api.api.schemas.common import PaginationMeta


class PaginationParams:
    """Reusable limit/offset query parameters."""

    def __init__(
        self,
        limit: Annotated[int, Query(ge=1, le=200, description="Page size")] = 50,
        offset: Annotated[int, Query(ge=0, description="Items to skip")] = 0,
    ) -> None:
        self.limit = limit
        self.offset = offset

    def to_meta(self, total: int) -> PaginationMeta:
        return PaginationMeta(total=total, limit=self.limit, offset=self.offset)


def not_implemented(feature: str = "This endpoint") -> None:
    """Raise 501 for contract-only routes (implemented in Milestone 4)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "type": "about:blank",
            "title": "Not Implemented",
            "status": 501,
            "detail": f"{feature} will be implemented in Milestone 4 (backend).",
            "code": "not_implemented",
        },
    )
