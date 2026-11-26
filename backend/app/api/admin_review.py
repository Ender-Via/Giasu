from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_audit_log_service, require_roles
from app.api.notifications import get_notification_service
from app.core.constants import ROLE_ADMIN
from app.core.file_storage import FileStorage, get_file_storage
from app.db.session import get_db
from app.repositories.admin_review import AdminReviewRepository
from app.schemas.admin_review import (
    AdminTutorProfileListItemResponse,
    AdminTutorProfilePageResponse,
    AdminTutorRequestPageResponse,
    RejectModerationRequest,
)
from app.schemas.auth import CurrentUserResponse
from app.schemas.common import ApiResponse
from app.schemas.recruitment import TutorRequestAdminResponse
from app.services.admin_review import AdminReviewService
from app.services.audit_logs import AuditLogService
from app.services.notifications import NotificationService

router = APIRouter(prefix="/api", tags=["AdminReview"])

AdminUser = Annotated[CurrentUserResponse, Depends(require_roles(ROLE_ADMIN))]


def get_admin_review_service(
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[FileStorage, Depends(get_file_storage)],
    notifications: Annotated[NotificationService, Depends(get_notification_service)],
    audit: Annotated[AuditLogService, Depends(get_audit_log_service)],
) -> AdminReviewService:
    return AdminReviewService(AdminReviewRepository(db), storage, notifications, audit)


Service = Annotated[AdminReviewService, Depends(get_admin_review_service)]


@router.get("/tutor-profiles", response_model=ApiResponse[AdminTutorProfilePageResponse])
def list_tutor_profiles_for_admin(
    current_user: AdminUser,
    service: Service,
    status: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    pageSize: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ApiResponse[AdminTutorProfilePageResponse]:
    del current_user
    return ApiResponse[AdminTutorProfilePageResponse].ok(
        service.list_tutor_profiles(status=status, page=page, page_size=pageSize)
    )


@router.post(
    "/tutor-profiles/{profile_id}/approve",
    response_model=ApiResponse[AdminTutorProfileListItemResponse],
)
def approve_tutor_profile(
    profile_id: UUID, current_user: AdminUser, service: Service
) -> ApiResponse[AdminTutorProfileListItemResponse]:
    return ApiResponse[AdminTutorProfileListItemResponse].ok(
        service.approve_tutor_profile(current_user.userId, profile_id)
    )


@router.post(
    "/tutor-profiles/{profile_id}/reject",
    response_model=ApiResponse[AdminTutorProfileListItemResponse],
)
def reject_tutor_profile(
    profile_id: UUID,
    body: RejectModerationRequest,
    current_user: AdminUser,
    service: Service,
) -> ApiResponse[AdminTutorProfileListItemResponse]:
    return ApiResponse[AdminTutorProfileListItemResponse].ok(
        service.reject_tutor_profile(current_user.userId, profile_id, body.reason or "")
    )


@router.get("/tutor-requests", response_model=ApiResponse[AdminTutorRequestPageResponse])
def list_tutor_requests_for_admin(
    current_user: AdminUser,
    service: Service,
    status: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    pageSize: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ApiResponse[AdminTutorRequestPageResponse]:
    del current_user
    return ApiResponse[AdminTutorRequestPageResponse].ok(
        service.list_tutor_requests(status=status, page=page, page_size=pageSize)
    )


@router.post(
    "/tutor-requests/{request_id}/approve",
    response_model=ApiResponse[TutorRequestAdminResponse],
)
def approve_tutor_request(
    request_id: UUID, current_user: AdminUser, service: Service
) -> ApiResponse[TutorRequestAdminResponse]:
    return ApiResponse[TutorRequestAdminResponse].ok(
        service.approve_tutor_request(current_user.userId, request_id)
    )


@router.post(
    "/tutor-requests/{request_id}/reject",
    response_model=ApiResponse[TutorRequestAdminResponse],
)
def reject_tutor_request(
    request_id: UUID,
    body: RejectModerationRequest,
    current_user: AdminUser,
    service: Service,
) -> ApiResponse[TutorRequestAdminResponse]:
    return ApiResponse[TutorRequestAdminResponse].ok(
        service.reject_tutor_request(current_user.userId, request_id, body.reason or "")
    )
