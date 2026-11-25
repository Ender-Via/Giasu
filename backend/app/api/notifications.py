from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.core.constants import ROLE_ADMIN, ROLE_PARENT, ROLE_TUTOR
from app.core.email_sender import EmailSender, get_email_sender
from app.db.session import get_db
from app.repositories.notifications import NotificationRepository
from app.schemas.auth import CurrentUserResponse
from app.schemas.common import ApiResponse
from app.schemas.notifications import (
    NotificationPageResponse,
    NotificationPreferencesResponse,
    UnreadCountResponse,
    UpdateNotificationPreferencesRequest,
)
from app.services.notifications import NotificationService

router = APIRouter(prefix="/api", tags=["Notifications"])

AnyUser = Annotated[
    CurrentUserResponse,
    Depends(require_roles(ROLE_ADMIN, ROLE_TUTOR, ROLE_PARENT)),
]


def get_notification_service(
    db: Annotated[Session, Depends(get_db)],
    email_sender: Annotated[EmailSender, Depends(get_email_sender)],
) -> NotificationService:
    return NotificationService(NotificationRepository(db), email_sender)


Service = Annotated[NotificationService, Depends(get_notification_service)]


@router.get("/notifications", response_model=ApiResponse[NotificationPageResponse])
def list_notifications(
    current_user: AnyUser,
    service: Service,
    unreadOnly: bool = False,
    page: Annotated[int, Query(ge=1)] = 1,
    pageSize: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ApiResponse[NotificationPageResponse]:
    result = service.list_mine(
        current_user.userId,
        unread_only=unreadOnly,
        page=page,
        page_size=pageSize,
    )
    return ApiResponse[NotificationPageResponse].ok(result)


@router.get("/notifications/unread-count", response_model=ApiResponse[UnreadCountResponse])
def get_unread_count(
    current_user: AnyUser, service: Service
) -> ApiResponse[UnreadCountResponse]:
    count = service.get_unread_count(current_user.userId)
    return ApiResponse[UnreadCountResponse].ok(UnreadCountResponse(count=count))


@router.post("/notifications/{notification_id}/read", response_model=ApiResponse[None])
def mark_notification_read(
    notification_id: UUID, current_user: AnyUser, service: Service
) -> ApiResponse[None]:
    service.mark_read(current_user.userId, notification_id)
    return ApiResponse[None].ok(None)


@router.post("/notifications/read-all", response_model=ApiResponse[None])
def mark_all_notifications_read(
    current_user: AnyUser, service: Service
) -> ApiResponse[None]:
    service.mark_all_read(current_user.userId)
    return ApiResponse[None].ok(None)


@router.get(
    "/notification-preferences",
    response_model=ApiResponse[NotificationPreferencesResponse],
)
def get_notification_preferences(
    current_user: AnyUser, service: Service
) -> ApiResponse[NotificationPreferencesResponse]:
    result = service.get_preferences(current_user.userId, current_user.role)
    return ApiResponse[NotificationPreferencesResponse].ok(result)


@router.put(
    "/notification-preferences",
    response_model=ApiResponse[NotificationPreferencesResponse],
)
def update_notification_preferences(
    body: UpdateNotificationPreferencesRequest,
    current_user: AnyUser,
    service: Service,
) -> ApiResponse[NotificationPreferencesResponse]:
    result = service.update_preferences(
        current_user.userId, current_user.role, body.items or []
    )
    return ApiResponse[NotificationPreferencesResponse].ok(result)
