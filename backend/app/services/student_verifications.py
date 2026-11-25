import logging
from uuid import UUID, uuid4

from app.core.clock import as_utc, as_utc_or_none, utc_now
from app.core.constants import NotificationType, VerificationStatus
from app.core.file_storage import SIGNED_URL_TTL_SECONDS, FileStorage, FileStorageError
from app.core.file_validation import (
    STORAGE_EXTENSIONS,
    IncomingFile,
    ValidatedFile,
    validate_evidence_file,
)
from app.db.models import StudentVerification
from app.repositories.student_verifications import StudentVerificationRepository
from app.schemas.student_verifications import (
    MSG_INVALID_STATUS,
    MSG_STUDENT_CODE,
    MSG_UNIVERSITY,
    AdminVerificationDetailResponse,
    AdminVerificationListItemResponse,
    AdminVerificationPageResponse,
    TutorVerificationResponse,
    validate_student_code,
    validate_university,
)
from app.services.errors import ConflictError, InvalidInputError, NotFoundError
from app.services.notifications import NotificationService

logger = logging.getLogger(__name__)

MSG_TUTOR_NOT_FOUND = "Không tìm thấy tài khoản gia sư."
MSG_VERIFICATION_NOT_FOUND = "Không tìm thấy yêu cầu xác thực."
MSG_DUPLICATE_SUBMISSION = "Bạn đang có yêu cầu chờ xác thực hoặc đã xác thực sinh viên."
MSG_NOT_PENDING = "Chỉ xử lý được yêu cầu đang chờ xác thực."
MSG_FILE_REQUIRED = "Vui lòng chọn một tệp minh chứng."

ADMIN_FILTER_STATUSES = (
    VerificationStatus.PENDING,
    VerificationStatus.VERIFIED,
    VerificationStatus.REJECTED,
)


def _to_tutor_response(item: StudentVerification) -> TutorVerificationResponse:
    return TutorVerificationResponse(
        id=item.id,
        university=item.university,
        studentCode=item.student_code,
        status=item.status,
        rejectReason=item.reject_reason,
        createdAtUtc=as_utc(item.created_at),
        reviewedAtUtc=as_utc_or_none(item.reviewed_at),
    )


def _to_admin_item(item: StudentVerification) -> AdminVerificationListItemResponse:
    return AdminVerificationListItemResponse(
        id=item.id,
        tutorId=item.tutor_id,
        tutorName=item.tutor.user.full_name,
        tutorEmail=item.tutor.user.login_identifier,
        university=item.university,
        studentCode=item.student_code,
        status=item.status,
        rejectReason=item.reject_reason,
        reviewedByName=item.reviewer.full_name if item.reviewer is not None else None,
        reviewedAtUtc=as_utc_or_none(item.reviewed_at),
        createdAtUtc=as_utc(item.created_at),
    )


def _validate_submission(
    university: str | None,
    student_code: str | None,
    incoming_file: IncomingFile | None,
) -> tuple[str, str, ValidatedFile]:
    errors: list[str] = []
    clean_university = validate_university(university)
    if clean_university is None:
        errors.append(MSG_UNIVERSITY)

    clean_code = validate_student_code(student_code)
    if clean_code is None:
        errors.append(MSG_STUDENT_CODE)

    validated_file: ValidatedFile | None = None
    if incoming_file is None:
        errors.append(MSG_FILE_REQUIRED)
    else:
        validated_file, file_error = validate_evidence_file(incoming_file)
        if file_error is not None:
            errors.append(file_error)

    if errors or clean_university is None or clean_code is None or validated_file is None:
        raise InvalidInputError(errors=errors)
    return clean_university, clean_code, validated_file


class StudentVerificationService:
    def __init__(
        self,
        verifications: StudentVerificationRepository,
        storage: FileStorage,
        notifications: NotificationService,
    ) -> None:
        self.verifications = verifications
        self.storage = storage
        self.notifications = notifications

    def get_mine(self, tutor_id: UUID) -> TutorVerificationResponse | None:
        latest = self.verifications.get_latest_for_tutor(tutor_id)
        return _to_tutor_response(latest) if latest is not None else None

    def submit(
        self,
        tutor_id: UUID,
        university: str | None,
        student_code: str | None,
        incoming_file: IncomingFile | None,
    ) -> TutorVerificationResponse:
        clean_university, clean_code, validated_file = _validate_submission(
            university, student_code, incoming_file
        )
        tutor = self.verifications.get_tutor(tutor_id)
        if tutor is None:
            raise NotFoundError(MSG_TUTOR_NOT_FOUND)
        if self.verifications.has_pending_or_verified(tutor_id):
            raise ConflictError(MSG_DUPLICATE_SUBMISSION)
        self.verifications.rollback()

        verification_id = uuid4()
        path = (
            f"student-verifications/{tutor_id}/{verification_id}"
            f"{STORAGE_EXTENSIONS[validated_file.content_type]}"
        )
        self.storage.upload(path, validated_file.data, validated_file.content_type)

        try:
            locked_tutor = self.verifications.lock_tutor(tutor_id)
            if locked_tutor is None:
                raise NotFoundError(MSG_TUTOR_NOT_FOUND)
            if self.verifications.has_pending_or_verified(tutor_id):
                raise ConflictError(MSG_DUPLICATE_SUBMISSION)

            now = utc_now()
            verification = StudentVerification(
                id=verification_id,
                tutor_id=tutor_id,
                university=clean_university,
                student_code=clean_code,
                evidence_file_ref=path,
                status=VerificationStatus.PENDING,
                created_at=now,
            )
            self.verifications.add(verification)
            locked_tutor.verification_status = VerificationStatus.PENDING
            pending_emails = self.notifications.queue_for_active_admins(
                NotificationType.MODERATION_QUEUE,
                "Yêu cầu xác thực sinh viên mới",
                f"Gia sư vừa gửi yêu cầu xác thực tại {clean_university} ({clean_code}).",
                link="/admin/student-verifications",
            )
            self.verifications.commit()
        except Exception:
            self.verifications.rollback()
            self._delete_quietly(path)
            raise

        self.notifications.dispatch_emails(pending_emails)
        return _to_tutor_response(verification)

    def list_for_admin(
        self, *, status: str | None, page: int, page_size: int
    ) -> AdminVerificationPageResponse:
        normalized_status = status.strip() if isinstance(status, str) else None
        if normalized_status == "":
            normalized_status = None
        if normalized_status is not None and normalized_status not in ADMIN_FILTER_STATUSES:
            raise InvalidInputError(errors=[MSG_INVALID_STATUS])

        items, total_count = self.verifications.list_for_admin(
            status=normalized_status, page=page, page_size=page_size
        )
        return AdminVerificationPageResponse(
            items=[_to_admin_item(item) for item in items],
            page=page,
            pageSize=page_size,
            totalCount=total_count,
        )

    def get_detail(self, verification_id: UUID) -> AdminVerificationDetailResponse:
        item = self.verifications.get_by_id(verification_id)
        if item is None:
            raise NotFoundError(MSG_VERIFICATION_NOT_FOUND)
        base = _to_admin_item(item)
        phone = item.tutor.phone
        file_ref = item.evidence_file_ref
        self.verifications.rollback()

        evidence_url: str | None = None
        try:
            signed = self.storage.create_signed_urls([file_ref], SIGNED_URL_TTL_SECONDS)
            evidence_url = signed.get(file_ref)
        except FileStorageError:
            logger.warning("Không tạo được URL ký cho yêu cầu xác thực %s", verification_id)

        return AdminVerificationDetailResponse(
            **base.model_dump(),
            tutorPhone=phone,
            evidenceUrl=evidence_url,
        )

    def approve(
        self, admin_id: UUID, verification_id: UUID
    ) -> AdminVerificationListItemResponse:
        now = utc_now()
        if not self.verifications.transition_from_pending(
            verification_id,
            to_status=VerificationStatus.VERIFIED,
            reviewed_by=admin_id,
            reviewed_at=now,
        ):
            self._raise_not_found_or_conflict(verification_id)

        item = self.verifications.get_by_id(verification_id)
        if item is None:
            raise NotFoundError(MSG_VERIFICATION_NOT_FOUND)
        self.verifications.update_tutor_verification_status(
            item.tutor_id, VerificationStatus.VERIFIED
        )
        pending_emails = self.notifications.queue_many(
            [item.tutor_id],
            NotificationType.MODERATION_RESULT,
            "Xác thực sinh viên thành công",
            "Yêu cầu xác thực sinh viên của bạn đã được duyệt. Hồ sơ hiện có huy hiệu Đã xác thực.",
            link="/tutor/verification",
        )
        self.verifications.commit()
        self.notifications.dispatch_emails(pending_emails)
        return _to_admin_item(item)

    def reject(
        self, admin_id: UUID, verification_id: UUID, reason: str
    ) -> AdminVerificationListItemResponse:
        now = utc_now()
        if not self.verifications.transition_from_pending(
            verification_id,
            to_status=VerificationStatus.REJECTED,
            reviewed_by=admin_id,
            reviewed_at=now,
            reject_reason=reason,
        ):
            self._raise_not_found_or_conflict(verification_id)

        item = self.verifications.get_by_id(verification_id)
        if item is None:
            raise NotFoundError(MSG_VERIFICATION_NOT_FOUND)
        self.verifications.update_tutor_verification_status(
            item.tutor_id, VerificationStatus.REJECTED
        )
        pending_emails = self.notifications.queue_many(
            [item.tutor_id],
            NotificationType.MODERATION_RESULT,
            "Yêu cầu xác thực sinh viên bị từ chối",
            f"Lý do: {reason}",
            link="/tutor/verification",
        )
        self.verifications.commit()
        self.notifications.dispatch_emails(pending_emails)
        return _to_admin_item(item)

    def _raise_not_found_or_conflict(self, verification_id: UUID) -> None:
        if self.verifications.get_by_id(verification_id) is None:
            raise NotFoundError(MSG_VERIFICATION_NOT_FOUND)
        raise ConflictError(MSG_NOT_PENDING)

    def _delete_quietly(self, path: str) -> None:
        try:
            self.storage.delete([path])
        except FileStorageError:
            logger.warning("Không xóa được tệp xác thực trên Storage, cần dọn tay: %s", path)
