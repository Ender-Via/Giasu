from datetime import datetime
from uuid import UUID, uuid4

from app.core.clock import as_utc, as_utc_or_none, utc_now
from app.core.constants import ROLE_ADMIN, ROLE_PARENT, ROLE_TUTOR, NotificationType
from app.core.recruitment_status import TutorApplicationStatus, TutorRequestStatus
from app.db.models import Student, Subject, TutorRequest
from app.repositories.audit_logs import AuditLogRepository
from app.repositories.recruitment import RecruitmentRepository
from app.repositories.subjects import SubjectRepository
from app.schemas.auth import CurrentUserResponse
from app.schemas.recruitment import (
    FIELD_MESSAGES,
    RequestParentResponse,
    StudentResponse,
    StudentUpsertRequest,
    TutorRequestAdminResponse,
    TutorRequestPageResponse,
    TutorRequestPublicResponse,
    TutorRequestResponse,
    TutorRequestUpsertRequest,
)
from app.services.audit_logs import AuditLogService, as_audit_service
from app.services.errors import ConflictError, InvalidInputError, NotFoundError
from app.services.notifications import NotificationService, PendingEmail

STUDENT_NOT_FOUND = "Không tìm thấy học sinh."
REQUEST_NOT_FOUND = "Không tìm thấy tin."


def student_response(student: Student) -> StudentResponse:
    return StudentResponse(
        id=student.id,
        fullName=student.full_name,
        gradeLevel=student.grade_level,
        createdAtUtc=as_utc(student.created_at),
    )


def request_response(request: TutorRequest, open_count: int) -> TutorRequestResponse:
    return TutorRequestResponse(
        id=request.id,
        title=request.title,
        studentId=request.student_id,
        studentName=request.student.full_name,
        studentGradeLevel=request.student.grade_level,
        subjectId=request.subject_id,
        subjectName=request.subject.name,
        educationLevel=request.education_level,
        teachingMode=request.teaching_mode,
        province=request.province,
        ward=request.ward,
        address=request.address,
        sessionsPerWeek=request.sessions_per_week,
        minFee=request.min_fee,
        maxFee=request.max_fee,
        requirements=request.requirements,
        status=request.status,
        openApplicationCount=open_count,
        rejectReason=request.reject_reason,
        expiresAtUtc=as_utc_or_none(request.expires_at),
        submittedAtUtc=as_utc(request.submitted_at),
        reviewedAtUtc=as_utc_or_none(request.reviewed_at),
        createdAtUtc=as_utc(request.created_at),
        updatedAtUtc=as_utc(request.updated_at),
    )


def apply_request_content(
    request: TutorRequest, body: TutorRequestUpsertRequest, student: Student, subject: Subject
) -> None:
    request.student_id = student.id
    request.student = student
    request.subject_id = subject.id
    request.subject = subject
    if "title" in body.model_fields_set:
        request.title = body.title
    request.education_level = body.educationLevel
    request.teaching_mode = body.teachingMode
    request.province = body.province
    request.ward = body.ward
    request.address = body.address
    request.sessions_per_week = body.sessionsPerWeek
    request.min_fee = body.minFee
    request.max_fee = body.maxFee
    request.requirements = body.requirements


class RecruitmentService:
    def __init__(
        self,
        repository: RecruitmentRepository,
        subjects: SubjectRepository,
        audit: AuditLogService | AuditLogRepository,
        notifications: NotificationService,
    ) -> None:
        self.repository = repository
        self.subjects = subjects
        self.audit = as_audit_service(audit)
        self.notifications = notifications

    def list_students(self, parent_id: UUID) -> list[StudentResponse]:
        return [student_response(student) for student in self.repository.list_students(parent_id)]

    def create_student(self, parent_id: UUID, body: StudentUpsertRequest) -> StudentResponse:
        if self.repository.get_parent(parent_id) is None:
            raise NotFoundError("Không tìm thấy hồ sơ phụ huynh.")
        student = Student(
            parent_id=parent_id,
            full_name=body.fullName,
            grade_level=body.gradeLevel,
            created_at=utc_now(),
        )
        self.repository.add(student)
        self.repository.commit()
        return student_response(student)

    def update_student(
        self, parent_id: UUID, student_id: UUID, body: StudentUpsertRequest
    ) -> StudentResponse:
        student = self._get_student(parent_id, student_id)
        student.full_name = body.fullName
        student.grade_level = body.gradeLevel
        self.repository.commit()
        return student_response(student)

    def list_requests(
        self,
        parent_id: UUID,
        status: str | None,
        student_id: UUID | None,
        page: int,
        page_size: int,
    ) -> TutorRequestPageResponse:
        requests, total = self.repository.list_requests(
            parent_id, status, student_id, page, page_size
        )
        return TutorRequestPageResponse(
            items=[request_response(request, count) for request, count in requests],
            page=page,
            pageSize=page_size,
            totalCount=total,
        )

    def get_request(
        self, current_user: CurrentUserResponse, request_id: UUID
    ) -> TutorRequestAdminResponse | TutorRequestResponse | TutorRequestPublicResponse:
        request = self.repository.get_request(
            request_id,
            parent_id=current_user.userId if current_user.role == ROLE_PARENT else None,
            recruiting_only=current_user.role == ROLE_TUTOR,
        )
        if request is None:
            raise NotFoundError(REQUEST_NOT_FOUND)
        if current_user.role == ROLE_TUTOR:
            return TutorRequestPublicResponse(
                id=request.id,
                title=request.title,
                subjectName=request.subject.name,
                studentGradeLevel=request.student.grade_level,
                educationLevel=request.education_level,
                teachingMode=request.teaching_mode,
                province=request.province,
                ward=request.ward,
                sessionsPerWeek=request.sessions_per_week,
                minFee=request.min_fee,
                maxFee=request.max_fee,
                requirements=request.requirements,
                approvedAtUtc=as_utc_or_none(request.reviewed_at),
                hasOpenApplication=bool(
                    self.repository.count_open_applications(request.id, current_user.userId)
                ),
            )

        detail = request_response(request, self.repository.count_open_applications(request.id))
        if current_user.role == ROLE_ADMIN:
            user, parent = self.repository.get_parent_contact(request.parent_id)
            return TutorRequestAdminResponse(
                **detail.model_dump(),
                parent=RequestParentResponse(
                    id=user.id,
                    fullName=user.full_name,
                    email=user.login_identifier,
                    phone=parent.phone,
                ),
            )
        return detail

    def create_request(
        self, parent_id: UUID, body: TutorRequestUpsertRequest
    ) -> TutorRequestResponse:
        student = self._get_student(parent_id, body.studentId)
        subject = self._get_subject(body.subjectId)
        now = utc_now()
        request = TutorRequest(
            id=uuid4(),
            parent_id=parent_id,
            status=TutorRequestStatus.PENDING_REVIEW,
            submitted_at=now,
            created_at=now,
            updated_at=now,
        )
        apply_request_content(request, body, student, subject)
        self.repository.add(request)
        self._log_request(request, "Create", None, now)
        pending = self._queue_moderation(request)
        response = request_response(request, 0)
        self.repository.commit()
        self.notifications.dispatch_emails(pending)
        return response

    def update_request(
        self, parent_id: UUID, request_id: UUID, body: TutorRequestUpsertRequest
    ) -> TutorRequestResponse:
        request = self._lock_request(parent_id, request_id)
        previous = request.status
        if previous not in TutorRequestStatus.EDITABLE:
            raise ConflictError("Tin đã tuyển hoặc đã đóng, không sửa được.")
        student = self._get_student(parent_id, body.studentId)
        subject = self._get_subject(body.subjectId)
        now = utc_now()
        apply_request_content(request, body, student, subject)
        request.updated_at = now

        pending: list[PendingEmail] = []
        if previous != TutorRequestStatus.PENDING_REVIEW:
            request.status = TutorRequestStatus.PENDING_REVIEW
            request.submitted_at = now
            request.expires_at = None
            self._log_request(request, "Resubmit", previous, now)
            pending = self._queue_moderation(request)
        response = request_response(request, self.repository.count_open_applications(request.id))
        self.repository.commit()
        self.notifications.dispatch_emails(pending)
        return response

    def close_request(self, parent_id: UUID, request_id: UUID) -> TutorRequestResponse:
        request = self._lock_request(parent_id, request_id)
        if request.status != TutorRequestStatus.RECRUITING:
            raise ConflictError("Chỉ có thể đóng tin đang tuyển.")
        now = utc_now()
        request.status = TutorRequestStatus.CLOSED
        request.updated_at = now
        self._log_request(request, "Close", TutorRequestStatus.RECRUITING, now)

        recipients = []
        for application in self.repository.lock_open_applications(request.id):
            previous = application.status
            application.status = TutorApplicationStatus.CLOSE_TRANSITIONS[previous]
            application.updated_at = now
            self.audit.record_transition(
                actor_id=parent_id,
                entity="TutorApplication",
                entity_id=application.id,
                action="CloseRequest",
                from_status=previous,
                to_status=application.status,
                created_at=now,
            )
            recipients.append(application.tutor_id)

        pending = self.notifications.queue_many(
            recipients,
            NotificationType.APPLICATION_STATUS,
            "Tin tìm gia sư đã đóng",
            "Phụ huynh đã đóng tin. Phiếu ứng tuyển của bạn đã được cập nhật.",
            link="/tutor/applications",
        )
        response = request_response(request, 0)
        self.repository.commit()
        self.notifications.dispatch_emails(pending)
        return response

    def _get_student(self, parent_id: UUID, student_id: UUID) -> Student:
        student = self.repository.get_student(parent_id, student_id)
        if student is None:
            raise NotFoundError(STUDENT_NOT_FOUND)
        return student

    def _get_subject(self, subject_id: int) -> Subject:
        subjects = self.subjects.find_by_ids([subject_id])
        if not subjects:
            raise InvalidInputError(errors=[FIELD_MESSAGES["subjectId"]])
        return subjects[0]

    def _lock_request(self, parent_id: UUID, request_id: UUID) -> TutorRequest:
        request = self.repository.get_request(request_id, parent_id=parent_id, for_update=True)
        if request is None:
            raise NotFoundError(REQUEST_NOT_FOUND)
        return request

    def _queue_moderation(self, request: TutorRequest) -> list[PendingEmail]:
        return self.notifications.queue_for_active_admins(
            NotificationType.MODERATION_QUEUE,
            "Tin tìm gia sư chờ duyệt",
            f"Có tin tìm gia sư môn {request.subject.name} vừa được gửi duyệt.",
            link="/admin/jobs",
        )

    def _log_request(
        self, request: TutorRequest, action: str, previous: str | None, now: datetime
    ) -> None:
        self.audit.record_transition(
            actor_id=request.parent_id,
            entity="TutorRequest",
            entity_id=request.id,
            action=action,
            from_status=previous,
            to_status=request.status,
            created_at=now,
        )
