from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.core.supabase_auth import SupabaseAuthClient, get_supabase_auth_client
from app.db.session import get_db
from app.repositories.auth import AuthRepository
from app.schemas.auth import CurrentUserResponse, RegisterRequest
from app.schemas.common import ApiResponse
from app.services.auth import (
    AuthService,
    DuplicateEmailError,
    RegistrationRateLimitError,
    RegistrationUnavailableError,
)

router = APIRouter(prefix="/api/auth", tags=["Auth"])


def _get_client_ip(request: Request) -> str | None:
    client_host = request.client.host if request.client else None
    if client_host and client_host in get_settings().trusted_proxies:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return client_host


@router.post(
    "/register",
    response_model=ApiResponse[CurrentUserResponse],
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    supabase: Annotated[SupabaseAuthClient, Depends(get_supabase_auth_client)],
) -> ApiResponse[CurrentUserResponse]:
    service = AuthService(AuthRepository(db))
    try:
        user = service.register(payload, supabase, _get_client_ip(request))
    except DuplicateEmailError as exc:
        raise HTTPException(status_code=409, detail="Email đã được sử dụng.") from exc
    except RegistrationRateLimitError as exc:
        raise HTTPException(
            status_code=429,
            detail="Bạn đã thử đăng ký quá nhiều lần. Vui lòng thử lại sau 60 giây.",
        ) from exc
    except RegistrationUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail="Chưa thể tạo tài khoản, vui lòng thử lại sau.",
        ) from exc
    return ApiResponse[CurrentUserResponse].ok(user, "Tạo tài khoản thành công.")


@router.get("/me", response_model=ApiResponse[CurrentUserResponse])
def get_me(
    current_user: Annotated[CurrentUserResponse, Depends(get_current_user)],
) -> ApiResponse[CurrentUserResponse]:
    return ApiResponse[CurrentUserResponse].ok(current_user)
