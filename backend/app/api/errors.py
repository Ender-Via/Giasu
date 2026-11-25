from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.schemas.common import ApiResponse
from app.services.errors import ConflictError, InvalidInputError, NotFoundError, ServiceError

_STATUS_BY_ERROR: dict[type[ServiceError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    InvalidInputError: status.HTTP_400_BAD_REQUEST,
}


def register_service_error_handlers(application: FastAPI) -> None:
    async def handle_service_error(request: Request, exc: ServiceError) -> JSONResponse:
        del request
        status_code = next(
            code for error_type, code in _STATUS_BY_ERROR.items() if isinstance(exc, error_type)
        )
        return JSONResponse(
            status_code=status_code,
            content=ApiResponse[object].fail(exc.message, exc.errors).model_dump(),
        )

    for error_type in _STATUS_BY_ERROR:
        application.add_exception_handler(error_type, handle_service_error)
