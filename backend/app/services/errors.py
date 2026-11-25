class ServiceError(Exception):
    def __init__(self, message: str | None = None, errors: list[str] | None = None) -> None:
        super().__init__(message or "; ".join(errors or []))
        self.message = message
        self.errors = errors


class NotFoundError(ServiceError):
    pass


class ConflictError(ServiceError):
    pass


class InvalidInputError(ServiceError):
    pass
