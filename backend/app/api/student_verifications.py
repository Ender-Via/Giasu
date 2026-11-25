from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.api.notifications import get_notification_service
from app.core.constants import ROLE_ADMIN, ROLE_TUTOR
from app.core.file_storage import FileStorage, get_file_storage
from app.core.file_validation import MAX_EVIDENCE_BYTES, IncomingFile
from app.db.session import get_db
from app.repositories.student_verifications import StudentVerificationRepository
from app.schemas.auth import CurrentUserResponse
from app.schemas.common import ApiResponse
from app.schemas.student_verifications import (
    AdminVerificationDetailResponse,
    AdminVerificationListItemResponse,
    AdminVerificationPageResponse,
    RejectVerificationRequest,
    TutorVerificationResponse,
)
from app.services.notifications import NotificationService
from app.services.student_verifications import StudentVerificationService

router = APIRouter(prefix="/api/student-verifications", tags=["StudentVerifications"])

TutorUser = Annotated[CurrentUserResponse, Depends(require_roles(ROLE_TUTOR))]
AdminUser = Annotated[CurrentUserResponse, Depends(require_roles(ROLE_ADMIN))]


def get_verification_service(
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[FileStorage, Depends(get_file_storage)],
    notifications: Annotated[NotificationService, Depends(get_notification_service)],
) -> StudentVerificationService:
    return StudentVerificationService(
        StudentVerificationRepository(db), storage, notifications
    )


Service = Annotated[StudentVerificationService, Depends(get_verification_service)]


def _read_capped(upload: UploadFile | None) -> IncomingFile | None:
    if upload is None or not (upload.filename or "").strip():
        return None
    data = upload.file.read(MAX_EVIDENCE_BYTES + 1)
    if not data:
        return None
    return IncomingFile(file_name=upload.filename or "", data=data)


@router.get("/mine", response_model=ApiResponse[TutorVerificationResponse | None])
def get_my_verification(
    current_user: TutorUser, service: Service
) -> ApiResponse[TutorVerificationResponse | None]:
    return ApiResponse[TutorVerificationResponse | None].ok(
        service.get_mine(current_user.userId)
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ApiResponse[TutorVerificationResponse],
)
def submit_verification(
    current_user: TutorUser,
    service: Service,
    university: Annotated[str | None, Form()] = None,
    studentCode: Annotated[str | None, Form()] = None,
    file: Annotated[UploadFile | None, File()] = None,
) -> ApiResponse[TutorVerificationResponse]:
    result = service.submit(
        current_user.userId, university, studentCode, _read_capped(file)
    )
    return ApiResponse[TutorVerificationResponse].ok(result)


@router.get("", response_model=ApiResponse[AdminVerificationPageResponse])
def list_verifications(
    current_user: AdminUser,
    service: Service,
    status: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    pageSize: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ApiResponse[AdminVerificationPageResponse]:
    del current_user
    result = service.list_for_admin(status=status, page=page, page_size=pageSize)
    return ApiResponse[AdminVerificationPageResponse].ok(result)


@router.get("/{verification_id}", response_model=ApiResponse[AdminVerificationDetailResponse])
def get_verification_detail(
    verification_id: UUID, current_user: AdminUser, service: Service
) -> ApiResponse[AdminVerificationDetailResponse]:
    del current_user
    return ApiResponse[AdminVerificationDetailResponse].ok(service.get_detail(verification_id))


@router.post(
    "/{verification_id}/approve",
    response_model=ApiResponse[AdminVerificationListItemResponse],
)
def approve_verification(
    verification_id: UUID, current_user: AdminUser, service: Service
) -> ApiResponse[AdminVerificationListItemResponse]:
    result = service.approve(current_user.userId, verification_id)
    return ApiResponse[AdminVerificationListItemResponse].ok(result)


@router.post(
    "/{verification_id}/reject",
    response_model=ApiResponse[AdminVerificationListItemResponse],
)
def reject_verification(
    verification_id: UUID,
    body: RejectVerificationRequest,
    current_user: AdminUser,
    service: Service,
) -> ApiResponse[AdminVerificationListItemResponse]:
    result = service.reject(current_user.userId, verification_id, body.reason or "")
    return ApiResponse[AdminVerificationListItemResponse].ok(result)
