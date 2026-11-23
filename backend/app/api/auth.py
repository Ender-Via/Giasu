from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.schemas.auth import CurrentUserResponse
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.get("/me", response_model=ApiResponse[CurrentUserResponse])
def get_me(
    current_user: Annotated[CurrentUserResponse, Depends(get_current_user)],
) -> ApiResponse[CurrentUserResponse]:
    return ApiResponse[CurrentUserResponse].ok(current_user)
