from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    message: str | None = None
    errors: list[str] | None = None

    @classmethod
    def ok(cls, data: T, message: str | None = None) -> "ApiResponse[T]":
        return cls(success=True, data=data, message=message, errors=None)

    @classmethod
    def fail(cls, message: str | None = None, errors: list[str] | None = None) -> "ApiResponse[T]":
        return cls(success=False, data=None, message=message, errors=errors)
