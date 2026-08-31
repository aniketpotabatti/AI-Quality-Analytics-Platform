"""Domain-specific exceptions mapped to HTTP problem details at the API boundary."""

from uuid import UUID


class DomainError(Exception):
    """Base class for all domain errors."""

    def __init__(self, message: str, *, code: str = "domain_error") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(DomainError):
    def __init__(self, resource: str, identifier: UUID | str) -> None:
        super().__init__(
            message=f"{resource} not found: {identifier}",
            code="not_found",
        )
        self.resource = resource
        self.identifier = identifier


class ConflictError(DomainError):
    def __init__(self, code: str = "conflict", message: str = "Conflict") -> None:
        super().__init__(message=message, code=code)


class UnauthorizedError(DomainError):
    def __init__(self, code: str = "unauthorized", message: str = "Unauthorized") -> None:
        super().__init__(message=message, code=code)


class AuthorizationError(DomainError):
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message=message, code="forbidden")


class ValidationError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="validation_error")
