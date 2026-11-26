from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.admin_review import AdminReviewService, get_admin_review_service
from app.api.dependencies import get_audit_log_service, require_roles
from app.api.notifications import get_notification_service
from app.core.constants import ROLE_ADMIN, ROLE_TUTOR
from app.core.file_storage import FileStorage, get_file_storage
from app.db.session import get_db
from app.repositories.subjects import SubjectRepository
from app.repositories.tutor_profiles import TutorProfileRepository
from app.schemas.admin_review import AdminTutorProfileDetailResponse
from app.schemas.auth import CurrentUserResponse
from app.schemas.common import ApiResponse
from app.schemas.tutor_profiles import (
    AvailabilityRequest,
    TutorProfileDetailResponse,
    TutorProfileResponse,
    TutorProfileUpsertRequest,
)
from app.services.audit_logs import AuditLogService
from app.services.notifications import NotificationService
from app.services.tutor_profiles import TutorProfileService

router = APIRouter(prefix="/api/tutor-profiles", tags=["TutorProfiles"])

TutorUser = Annotated[CurrentUserResponse, Depends(require_roles(ROLE_TUTOR))]
ProfileViewer = Annotated[CurrentUserResponse, Depends(require_roles(ROLE_TUTOR, ROLE_ADMIN))]
ProfileDetail = AdminTutorProfileDetailResponse | TutorProfileDetailResponse


def get_tutor_profile_service(
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[FileStorage, Depends(get_file_storage)],
    notifications: Annotated[NotificationService, Depends(get_notification_service)],
    audit: Annotated[AuditLogService, Depends(get_audit_log_service)],
) -> TutorProfileService:
    return TutorProfileService(
        TutorProfileRepository(db),
        SubjectRepository(db),
        storage,
        notifications,
        audit,
    )


Service = Annotated[TutorProfileService, Depends(get_tutor_profile_service)]
ProfileResult = ApiResponse[TutorProfileResponse]


@router.get("/mine", response_model=ApiResponse[list[TutorProfileResponse]])
def list_my_profiles(
    current_user: TutorUser, service: Service
) -> ApiResponse[list[TutorProfileResponse]]:
    return ApiResponse[list[TutorProfileResponse]].ok(service.list_mine(current_user.userId))


@router.get("/{profile_id}", response_model=ApiResponse[ProfileDetail])
def get_profile_detail(
    profile_id: UUID,
    current_user: ProfileViewer,
    service: Service,
    admin_service: Annotated[AdminReviewService, Depends(get_admin_review_service)],
) -> ApiResponse[ProfileDetail]:
    if current_user.role == ROLE_ADMIN:
        return ApiResponse[ProfileDetail].ok(admin_service.get_tutor_profile_detail(profile_id))
    return ApiResponse[ProfileDetail].ok(service.get_mine(current_user.userId, profile_id))


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ProfileResult)
def create_profile(
    body: TutorProfileUpsertRequest, current_user: TutorUser, service: Service
) -> ProfileResult:
    return ProfileResult.ok(service.create(current_user.userId, body))


@router.put("/{profile_id}", response_model=ProfileResult)
def update_profile(
    profile_id: UUID, body: TutorProfileUpsertRequest, current_user: TutorUser, service: Service
) -> ProfileResult:
    return ProfileResult.ok(service.update(current_user.userId, profile_id, body))


@router.post("/{profile_id}/set-default", response_model=ProfileResult)
def set_default_profile(
    profile_id: UUID, current_user: TutorUser, service: Service
) -> ProfileResult:
    return ProfileResult.ok(service.set_default(current_user.userId, profile_id))


@router.put("/{profile_id}/availability", response_model=ProfileResult)
def set_profile_availability(
    profile_id: UUID, body: AvailabilityRequest, current_user: TutorUser, service: Service
) -> ProfileResult:
    profile = service.set_availability(current_user.userId, profile_id, body.availability or "")
    return ProfileResult.ok(profile)


@router.post("/{profile_id}/submit", response_model=ProfileResult)
def submit_profile(profile_id: UUID, current_user: TutorUser, service: Service) -> ProfileResult:
    return ProfileResult.ok(service.submit(current_user.userId, profile_id))
