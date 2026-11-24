import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.auth import router as auth_router
from app.api.errors import register_service_error_handlers
from app.api.subjects import router as subjects_router
from app.api.tutor_profile_evidences import router as tutor_profile_evidences_router
from app.api.tutor_profiles import router as tutor_profiles_router
from app.core.config import get_settings
from app.core.request_limits import RequestBodyLimitMiddleware
from app.core.validation_errors import GENERIC_VALIDATION_MESSAGE
from app.schemas.common import ApiResponse

logger = logging.getLogger(__name__)

MAX_REQUEST_BODY_BYTES = 26 * 1024 * 1024


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="Gia Sư API",
        version="0.1.0",
        description="API FastAPI cho nền tảng tìm việc gia sư và quản lý quá trình dạy",
    )

    application.add_middleware(RequestBodyLimitMiddleware, max_bytes=MAX_REQUEST_BODY_BYTES)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.middleware("http")
    async def security_headers(request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    @application.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        del request
        detail = exc.detail if isinstance(exc.detail, str) else "Yêu cầu không hợp lệ."
        return JSONResponse(
            status_code=exc.status_code,
            content=ApiResponse[object].fail(detail).model_dump(),
            headers=exc.headers,
        )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        del request
        field_messages = {
            "role": "Vui lòng chọn vai trò Gia sư hoặc Phụ huynh.",
            "fullName": "Họ tên từ 2 đến 100 ký tự.",
            "phone": "Số điện thoại gồm 10 chữ số, bắt đầu bằng 0.",
            "email": "Email không đúng định dạng.",
            "password": "Mật khẩu từ 8 đến 128 ký tự, có cả chữ và số.",
            "acceptTerms": "Bạn cần đồng ý quy chế để tiếp tục.",
        }
        errors: list[str] = []
        for error in exc.errors():
            context_error = (error.get("ctx") or {}).get("error")
            if error.get("type") == "value_error" and context_error is not None:
                message = str(context_error)
            else:
                field = next(
                    (str(part) for part in reversed(error["loc"]) if isinstance(part, str)), ""
                )
                message = field_messages.get(field, GENERIC_VALIDATION_MESSAGE)
            if message not in errors:
                errors.append(message)
        return JSONResponse(
            status_code=400,
            content=ApiResponse[object]
            .fail(errors=errors or [GENERIC_VALIDATION_MESSAGE])
            .model_dump(),
        )

    register_service_error_handlers(application)

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Lỗi backend chưa xử lý tại %s", request.url.path, exc_info=exc)
        return JSONResponse(
            status_code=500,
            content=ApiResponse[object]
            .fail("Đã xảy ra lỗi hệ thống, vui lòng thử lại sau.")
            .model_dump(),
        )

    @application.get("/health", include_in_schema=False)
    def health() -> ApiResponse[dict[str, str]]:
        return ApiResponse[dict[str, str]].ok({"status": "ok"})

    application.include_router(auth_router)
    application.include_router(subjects_router)
    application.include_router(tutor_profiles_router)
    application.include_router(tutor_profile_evidences_router)
    return application


app = create_app()
