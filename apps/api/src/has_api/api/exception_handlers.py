"""Maps domain exceptions to RFC 7807 problem detail responses."""

from fastapi import Request
from fastapi.responses import JSONResponse

from has_api.api.schemas.common import ProblemDetail
from has_api.domain.exceptions import (
    AuthorizationError,
    ConflictError,
    DomainError,
    NotFoundError,
    ValidationError,
)

_STATUS_MAP: dict[type[DomainError], int] = {
    NotFoundError: 404,
    ValidationError: 422,
    ConflictError: 409,
    AuthorizationError: 403,
}


async def domain_exception_handler(_request: Request, exc: DomainError) -> JSONResponse:
    status = _STATUS_MAP.get(type(exc), 400)
    problem = ProblemDetail(
        title=exc.code.replace("_", " ").title(),
        status=status,
        detail=exc.message,
        code=exc.code,
    )
    return JSONResponse(
        status_code=status,
        content=problem.model_dump(),
        headers={"Content-Type": "application/problem+json"},
    )
