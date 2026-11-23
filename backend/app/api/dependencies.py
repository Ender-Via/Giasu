from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_auth_user
from app.db.session import get_db
from app.repositories.auth import AuthRepository
from app.schemas.auth import CurrentUserResponse
from app.services.auth import AccountLockedError, AuthService


def get_current_user(
    auth_user_id: Annotated[UUID, Depends(get_current_auth_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CurrentUserResponse:
    """Xác thực token và nạp tài khoản nghiệp vụ đang hoạt động cho mọi route bảo vệ."""
    service = AuthService(AuthRepository(db))
    try:
        current_user = service.get_current_user(auth_user_id)
    except AccountLockedError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không đúng.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy hồ sơ tài khoản.",
        )

    return current_user
