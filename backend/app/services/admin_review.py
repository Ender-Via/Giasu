import logging
from collections.abc import Sequence
from datetime import timedelta
from uuid import UUID

from app.core.clock import as_utc_or_none, utc_now
from app.core.constants import NotificationType, TutorProfileStatus
from app.core.file_storage import SIGNED_URL_TTL_SECONDS, FileStorage, FileStorageError
from app.core.recruitment_status import TutorRequestStatus
from app.db.models import TutorProfile, TutorRequest
from app.repositories.admin_review import AdminReviewRepository
from app.repositories.audit_logs import AuditLogRepository
from app.schemas.admin_review import (
    MSG_INVALID_PROFILE_STATUS,
    MSG_INVALID_REQUEST_STATUS,
    AdminTutorProfileDetailResponse,
    AdminTutorProfileListItemResponse,
    AdminTutorProfilePageResponse,
    AdminTutorRequestPageResponse,
    AdminTutorSummaryResponse,
)
from app.schemas.recruitment import RequestParentResponse, TutorRequestAdminResponse
from app.services.audit_logs import AuditLogService, as_audit_service
from app.services.errors import ConflictError, InvalidInputError, NotFoundError
from app.services.notifications import NotificationService
from app.services.recruitment import REQUEST_NOT_FOUND, request_response
from app.services.tutor_profile_mapping import (
    attach_evidence_urls,
    to_profile_detail,
    to_profile_response,
)
from app.services.tutor_profile_rules import MSG_PROFILE_NOT_FOUND

logger = logging.getLogger(__name__)

PROFILE_REVIEW_STATUSES = (
    TutorProfileStatus.PENDING_REVIEW,
    TutorProfileStatus.APPROVED,
    TutorProfileStatus.REJECTED,
)
REQUEST_EXPIRY_DAYS = 30
MSG_PROFILE_NOT_PENDING = "Chỉ xử lý được hồ sơ đang chờ duyệt."
MSG_REQUEST_NOT_PENDING = "Chỉ xử lý được tin đang chờ duyệt."


def _normalize_status_filter(
    status: str | None, *, default: str, allowed: Sequence[str], error_message: str
) -> str:
    cleaned = status.strip() if isinstance(status, str) else ""
    target = cleaned or default
    if target not in allowed:
        raise InvalidInputError(errors=[error_message])
    return target


def _tutor_summary(profile: TutorProfile) -> AdminTutorSummaryResponse:
    tutor = profile.tutor
    user = tutor.user
    return AdminTutorSummaryResponse(
        id=user.id,
        fullName=user.full_name,
        email=user.login_identifier,
        phone=tutor.phone,
        verificationStatus=tutor.verification_status,
    )


def _to_admin_profile_item(profile: TutorProfile) -> AdminTutorProfileListItemResponse:
    base = to_profile_response(profile)
    return AdminTutorProfileListItemResponse(
        **base.model_dump(),
        reviewedByName=profile.reviewer.full_name if profile.reviewer is not None else None,
        reviewedAtUtc=as_utc_or_none(profile.reviewed_at),
        tutor=_tutor_summary(profile),
    )


def _to_admin_request_item(request: TutorRequest, open_count: int) -> TutorRequestAdminResponse:
    base = request_response(request, open_count)
    parent = request.parent
    user = parent.user
    return TutorRequestAdminResponse(
        **base.model_dump(),
        reviewedByName=request.reviewer.full_name if request.reviewer is not None else None,
        parent=RequestParentResponse(
            id=user.id,
            fullName=user.full_name,
            email=user.login_identifier,
            phone=parent.phone,
        ),
    )


class AdminReviewService:
    def __init__(
        self,
        repository: AdminReviewRepository,
        storage: FileStorage,
        notifications: NotificationService,
        audit: AuditLogService | AuditLogRepository,
    ) -> None:
        self.repository = repository
        self.storage = storage
        self.notifications = notifications
        self.audit = as_audit_service(audit)

    def list_tutor_profiles(
        self, *, status: str | None, page: int, page_size: int
    ) -> AdminTutorProfilePageResponse:
        target_status = _normalize_status_filter(
            status,
            default=TutorProfileStatus.PENDING_REVIEW,
            allowed=PROFILE_REVIEW_STATUSES,
            error_message=MSG_INVALID_PROFILE_STATUS,
        )
        items, total = self.repository.list_tutor_profiles(
            status=target_status, page=page, page_size=page_size
        )
        return AdminTutorProfilePageResponse(
            items=[_to_admin_profile_item(item) for item in items],
            page=page,
            pageSize=page_size,
            totalCount=total,
        )

    def get_tutor_profile_detail(self, profile_id: UUID) -> AdminTutorProfileDetailResponse:
        profile = self.repository.get_tutor_profile(profile_id)
        if profile is None:
            raise NotFoundError(MSG_PROFILE_NOT_FOUND)
        file_refs = {evidence.id: evidence.file_ref for evidence in profile.evidences}
        detail = to_profile_detail(profile, {})
        summary = _tutor_summary(profile)
        reviewer_name = profile.reviewer.full_name if profile.reviewer is not None else None
        reviewed_at = as_utc_or_none(profile.reviewed_at)
        self.repository.rollback()

        signed_urls = self._sign_profile_evidences(profile_id, file_refs)
        detail_with_urls = attach_evidence_urls(detail, file_refs, signed_urls)
        return AdminTutorProfileDetailResponse(
            **detail_with_urls.model_dump(),
            reviewedByName=reviewer_name,
            reviewedAtUtc=reviewed_at,
            tutor=summary,
        )

    def approve_tutor_profile(
        self, admin_id: UUID, profile_id: UUID
    ) -> AdminTutorProfileListItemResponse:
        return self._moderate_tutor_profile(
            admin_id=admin_id,
            profile_id=profile_id,
            to_status=TutorProfileStatus.APPROVED,
            action="Approve",
            reject_reason=None,
        )

    def reject_tutor_profile(
        self, admin_id: UUID, profile_id: UUID, reason: str
    ) -> AdminTutorProfileListItemResponse:
        return self._moderate_tutor_profile(
            admin_id=admin_id,
            profile_id=profile_id,
            to_status=TutorProfileStatus.REJECTED,
            action="Reject",
            reject_reason=reason,
        )

    def list_tutor_requests(
        self, *, status: str | None, page: int, page_size: int
    ) -> AdminTutorRequestPageResponse:
        target_status = _normalize_status_filter(
            status,
            default=TutorRequestStatus.PENDING_REVIEW,
            allowed=TutorRequestStatus.ALL,
            error_message=MSG_INVALID_REQUEST_STATUS,
        )
        rows, total = self.repository.list_tutor_requests(
            status=target_status, page=page, page_size=page_size
        )
        return AdminTutorRequestPageResponse(
            items=[_to_admin_request_item(request, count) for request, count in rows],
            page=page,
            pageSize=page_size,
            totalCount=total,
        )

    def approve_tutor_request(self, admin_id: UUID, request_id: UUID) -> TutorRequestAdminResponse:
        return self._moderate_tutor_request(
            admin_id=admin_id,
            request_id=request_id,
            to_status=TutorRequestStatus.RECRUITING,
            action="Approve",
            reject_reason=None,
        )

    def reject_tutor_request(
        self, admin_id: UUID, request_id: UUID, reason: str
    ) -> TutorRequestAdminResponse:
        return self._moderate_tutor_request(
            admin_id=admin_id,
            request_id=request_id,
            to_status=TutorRequestStatus.REJECTED,
            action="Reject",
            reject_reason=reason,
        )

    def _moderate_tutor_profile(
        self,
        *,
        admin_id: UUID,
        profile_id: UUID,
        to_status: str,
        action: str,
        reject_reason: str | None,
    ) -> AdminTutorProfileListItemResponse:
        now = utc_now()
        if not self.repository.transition_tutor_profile(
            profile_id,
            to_status=to_status,
            reviewed_by=admin_id,
            reviewed_at=now,
            reject_reason=reject_reason,
        ):
            if self.repository.get_tutor_profile(profile_id) is None:
                raise NotFoundError(MSG_PROFILE_NOT_FOUND)
            raise ConflictError(MSG_PROFILE_NOT_PENDING)

        profile = self.repository.get_tutor_profile(profile_id, populate_existing=True)
        if profile is None:
            raise NotFoundError(MSG_PROFILE_NOT_FOUND)

        self.audit.record_transition(
            actor_id=admin_id,
            entity="TutorProfile",
            entity_id=profile_id,
            action=action,
            from_status=TutorProfileStatus.PENDING_REVIEW,
            to_status=to_status,
            created_at=now,
        )
        if to_status == TutorProfileStatus.APPROVED:
            title = "Hồ sơ gia sư đã được duyệt"
            message = (
                f'Hồ sơ "{profile.title}" đã được duyệt. Bạn có thể dùng hồ sơ này để ứng tuyển.'
            )
        else:
            title = "Hồ sơ gia sư bị từ chối"
            message = f'Hồ sơ "{profile.title}" bị từ chối. Lý do: {reject_reason}'

        pending_emails = self.notifications.queue_many(
            [profile.tutor_id],
            NotificationType.MODERATION_RESULT,
            title,
            message,
            link="/tutor/profiles",
        )
        item = _to_admin_profile_item(profile)
        self.repository.commit()
        self.notifications.dispatch_emails(pending_emails)
        return item

    def _moderate_tutor_request(
        self,
        *,
        admin_id: UUID,
        request_id: UUID,
        to_status: str,
        action: str,
        reject_reason: str | None,
    ) -> TutorRequestAdminResponse:
        now = utc_now()
        expires_at = (
            now + timedelta(days=REQUEST_EXPIRY_DAYS)
            if to_status == TutorRequestStatus.RECRUITING
            else None
        )
        if not self.repository.transition_tutor_request(
            request_id,
            to_status=to_status,
            reviewed_by=admin_id,
            reviewed_at=now,
            expires_at=expires_at,
            reject_reason=reject_reason,
        ):
            if self.repository.get_tutor_request(request_id) is None:
                raise NotFoundError(REQUEST_NOT_FOUND)
            raise ConflictError(MSG_REQUEST_NOT_PENDING)

        request = self.repository.get_tutor_request(request_id, populate_existing=True)
        if request is None:
            raise NotFoundError(REQUEST_NOT_FOUND)

        self.audit.record_transition(
            actor_id=admin_id,
            entity="TutorRequest",
            entity_id=request_id,
            action=action,
            from_status=TutorRequestStatus.PENDING_REVIEW,
            to_status=to_status,
            created_at=now,
        )
        if to_status == TutorRequestStatus.RECRUITING:
            title = "Tin tìm gia sư đã được duyệt"
            message = (
                f"Tin tìm gia sư môn {request.subject.name} đã được duyệt "
                "và hiển thị trong 30 ngày."
            )
        else:
            title = "Tin tìm gia sư bị từ chối"
            message = (
                f"Tin tìm gia sư môn {request.subject.name} bị từ chối. Lý do: {reject_reason}"
            )

        pending_emails = self.notifications.queue_many(
            [request.parent_id],
            NotificationType.MODERATION_RESULT,
            title,
            message,
            link="/parent/jobs",
        )
        open_count = self.repository.count_open_applications(request_id)
        item = _to_admin_request_item(request, open_count)
        self.repository.commit()
        self.notifications.dispatch_emails(pending_emails)
        return item

    def _sign_profile_evidences(
        self, profile_id: UUID, file_refs: dict[UUID, str]
    ) -> dict[str, str]:
        if not file_refs:
            return {}
        try:
            return self.storage.create_signed_urls(list(file_refs.values()), SIGNED_URL_TTL_SECONDS)
        except FileStorageError:
            logger.warning("Không tạo được URL ký cho minh chứng của hồ sơ %s", profile_id)
            return {}
