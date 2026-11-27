from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_audit_log_service, require_roles
from app.api.notifications import get_notification_service
from app.core.constants import ROLE_ADMIN, ROLE_PARENT, ROLE_TUTOR
from app.core.recruitment_status import TutorRequestStatusName
from app.db.session import get_db
from app.repositories.recruitment import RecruitmentRepository
from app.repositories.subjects import SubjectRepository
from app.schemas.auth import CurrentUserResponse
from app.schemas.common import ApiResponse
from app.schemas.recruitment import (
    StudentResponse,
    StudentUpsertRequest,
    TutorRequestAdminResponse,
    TutorRequestPageResponse,
    TutorRequestPublicResponse,
    TutorRequestResponse,
    TutorRequestUpsertRequest,
)
from app.services.audit_logs import AuditLogService
from app.services.notifications import NotificationService
from app.services.recruitment import RecruitmentService

router = APIRouter(prefix="/api")
ParentUser = Annotated[CurrentUserResponse, Depends(require_roles(ROLE_PARENT))]
RequestViewer = Annotated[
    CurrentUserResponse, Depends(require_roles(ROLE_PARENT, ROLE_ADMIN, ROLE_TUTOR))
]
RequestDetail = TutorRequestAdminResponse | TutorRequestResponse | TutorRequestPublicResponse


def get_recruitment_service(
    db: Annotated[Session, Depends(get_db)],
    notifications: Annotated[NotificationService, Depends(get_notification_service)],
    audit: Annotated[AuditLogService, Depends(get_audit_log_service)],
) -> RecruitmentService:
    return RecruitmentService(
        RecruitmentRepository(db), SubjectRepository(db), audit, notifications
    )


Service = Annotated[RecruitmentService, Depends(get_recruitment_service)]


@router.get("/students/mine", tags=["Students"])
def list_students(user: ParentUser, service: Service) -> ApiResponse[list[StudentResponse]]:
    return ApiResponse[list[StudentResponse]].ok(service.list_students(user.userId))


@router.post("/students", status_code=status.HTTP_201_CREATED, tags=["Students"])
def create_student(
    body: StudentUpsertRequest, user: ParentUser, service: Service
) -> ApiResponse[StudentResponse]:
    return ApiResponse[StudentResponse].ok(service.create_student(user.userId, body))


@router.put("/students/{id}", tags=["Students"])
def update_student(
    id: UUID, body: StudentUpsertRequest, user: ParentUser, service: Service
) -> ApiResponse[StudentResponse]:
    return ApiResponse[StudentResponse].ok(service.update_student(user.userId, id, body))


@router.get("/tutor-requests/mine", tags=["Tutor Requests"])
def list_requests(
    user: ParentUser,
    service: Service,
    status: TutorRequestStatusName | None = None,
    student_id: Annotated[UUID | None, Query(alias="studentId")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, alias="pageSize")] = 20,
) -> ApiResponse[TutorRequestPageResponse]:
    result = service.list_requests(user.userId, status, student_id, page, page_size)
    return ApiResponse[TutorRequestPageResponse].ok(result)


@router.get("/tutor-requests/{id}", tags=["Tutor Requests"])
def get_request(id: UUID, user: RequestViewer, service: Service) -> ApiResponse[RequestDetail]:
    return ApiResponse[RequestDetail].ok(service.get_request(user, id))


@router.post("/tutor-requests", status_code=status.HTTP_201_CREATED, tags=["Tutor Requests"])
def create_request(
    body: TutorRequestUpsertRequest, user: ParentUser, service: Service
) -> ApiResponse[TutorRequestResponse]:
    return ApiResponse[TutorRequestResponse].ok(service.create_request(user.userId, body))


@router.put("/tutor-requests/{id}", tags=["Tutor Requests"])
def update_request(
    id: UUID, body: TutorRequestUpsertRequest, user: ParentUser, service: Service
) -> ApiResponse[TutorRequestResponse]:
    return ApiResponse[TutorRequestResponse].ok(service.update_request(user.userId, id, body))


@router.post("/tutor-requests/{id}/close", tags=["Tutor Requests"])
def close_request(
    id: UUID, user: ParentUser, service: Service
) -> ApiResponse[TutorRequestResponse]:
    return ApiResponse[TutorRequestResponse].ok(service.close_request(user.userId, id))
