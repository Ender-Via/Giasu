import logging
from datetime import datetime
from uuid import UUID, uuid4

from app.core.clock import utc_now
from app.core.constants import Availability, NotificationType, TutorProfileStatus
from app.core.file_storage import SIGNED_URL_TTL_SECONDS, FileStorage, FileStorageError
from app.db.models import Subject, TutorProfile
from app.repositories.audit_logs import AuditLogRepository
from app.repositories.subjects import SubjectRepository
from app.repositories.tutor_profiles import TutorProfileRepository
from app.schemas.tutor_profiles import (
    TutorProfileDetailResponse,
    TutorProfileResponse,
    TutorProfileUpsertRequest,
)
from app.services.audit_logs import AuditLogService, as_audit_service
from app.services.errors import ConflictError, InvalidInputError, NotFoundError
from app.services.notifications import NotificationService, PendingEmail
from app.services.tutor_profile_mapping import (
    attach_evidence_urls,
    to_profile_detail,
    to_profile_response,
)
from app.services.tutor_profile_rules import (
    MAX_PROFILES_PER_TUTOR,
    MSG_PENDING_LOCKED,
    MSG_PROFILE_LIMIT,
    MSG_SUBMIT_STATE,
    MSG_TUTOR_NOT_FOUND,
    apply_content,
    content_differs,
    mark_pending_review,
    missing_submission_requirements,
    profile_not_found,
    resolve_subjects,
)

logger = logging.getLogger(__name__)


class TutorProfileService:
    def __init__(
        self,
        profiles: TutorProfileRepository,
        subjects: SubjectRepository,
        storage: FileStorage,
        notifications: NotificationService,
        audit: AuditLogService | AuditLogRepository,
    ) -> None:
        self.profiles = profiles
        self.subjects = subjects
        self.storage = storage
        self.notifications = notifications
        self.audit = as_audit_service(audit)

    def list_mine(self, tutor_id: UUID) -> list[TutorProfileResponse]:
        return [to_profile_response(p) for p in self.profiles.list_for_tutor(tutor_id)]

    def get_mine(self, tutor_id: UUID, profile_id: UUID) -> TutorProfileDetailResponse:
        profile = self.profiles.get_for_tutor(tutor_id, profile_id)
        if profile is None:
            raise profile_not_found()
        file_refs = {evidence.id: evidence.file_ref for evidence in profile.evidences}
        detail = to_profile_detail(profile, {})
        self.profiles.rollback()
        return attach_evidence_urls(detail, file_refs, self._signed_urls(profile_id, file_refs))

    def create(self, tutor_id: UUID, data: TutorProfileUpsertRequest) -> TutorProfileResponse:
        subjects = self._subjects_for(data)
        if not self.profiles.lock_tutor(tutor_id):
            raise NotFoundError(MSG_TUTOR_NOT_FOUND)

        existing = self.profiles.count_for_tutor(tutor_id)
        if existing >= MAX_PROFILES_PER_TUTOR:
            raise ConflictError(MSG_PROFILE_LIMIT)

        now = utc_now()
        profile = TutorProfile(
            id=uuid4(),
            tutor_id=tutor_id,
            status=TutorProfileStatus.DRAFT,
            availability=Availability.ACCEPTING,
            is_default=existing == 0,
            created_at=now,
            updated_at=now,
            evidences=[],
        )
        apply_content(profile, data, subjects)
        self.profiles.add(profile)
        self._record_transition(profile, "Create", None, now)
        self.profiles.commit()
        return to_profile_response(profile)

    def update(
        self, tutor_id: UUID, profile_id: UUID, data: TutorProfileUpsertRequest
    ) -> TutorProfileResponse:
        subjects = self._subjects_for(data)
        profile = self._locked_profile(tutor_id, profile_id)
        if profile.status == TutorProfileStatus.PENDING_REVIEW:
            raise ConflictError(MSG_PENDING_LOCKED)
        if not content_differs(profile, data, subjects):
            return to_profile_response(profile)

        now = utc_now()
        apply_content(profile, data, subjects)
        profile.updated_at = now
        pending_emails: list[PendingEmail] = []
        if profile.status == TutorProfileStatus.APPROVED:
            missing = missing_submission_requirements(profile)
            if missing:
                raise InvalidInputError(errors=missing)
            pending_emails = self._submit_for_review(profile, now)
        self.profiles.commit()
        self.notifications.dispatch_emails(pending_emails)
        return to_profile_response(profile)

    def set_default(self, tutor_id: UUID, profile_id: UUID) -> TutorProfileResponse:
        if not self.profiles.lock_tutor(tutor_id):
            raise profile_not_found()
        profile = self._locked_profile(tutor_id, profile_id)
        if not profile.is_default:
            self.profiles.clear_default(tutor_id)
            profile.is_default = True
            self.profiles.commit()
        return to_profile_response(profile)

    def set_availability(
        self, tutor_id: UUID, profile_id: UUID, availability: str
    ) -> TutorProfileResponse:
        profile = self._locked_profile(tutor_id, profile_id)
        if profile.availability != availability:
            profile.availability = availability
            self.profiles.commit()
        return to_profile_response(profile)

    def submit(self, tutor_id: UUID, profile_id: UUID) -> TutorProfileResponse:
        profile = self._locked_profile(tutor_id, profile_id)
        if profile.status not in TutorProfileStatus.EDITABLE_EVIDENCE:
            raise ConflictError(MSG_SUBMIT_STATE)
        missing = missing_submission_requirements(profile)
        if missing:
            raise InvalidInputError(errors=missing)

        pending_emails = self._submit_for_review(profile, utc_now())
        self.profiles.commit()
        self.notifications.dispatch_emails(pending_emails)
        return to_profile_response(profile)

    def _submit_for_review(self, profile: TutorProfile, now: datetime) -> list[PendingEmail]:
        previous = profile.status
        mark_pending_review(profile, now)
        self._record_transition(profile, "Submit", previous, now)
        return self.notifications.queue_for_active_admins(
            NotificationType.MODERATION_QUEUE,
            "Hồ sơ gia sư chờ duyệt",
            f'Hồ sơ "{profile.title}" vừa được gửi duyệt.',
            link="/admin/tutor-profiles",
        )

    def _record_transition(
        self, profile: TutorProfile, action: str, previous: str | None, now: datetime
    ) -> None:
        self.audit.record_transition(
            actor_id=profile.tutor_id,
            entity="TutorProfile",
            entity_id=profile.id,
            action=action,
            from_status=previous,
            to_status=profile.status,
            created_at=now,
        )

    def _locked_profile(self, tutor_id: UUID, profile_id: UUID) -> TutorProfile:
        profile = self.profiles.get_for_tutor(tutor_id, profile_id, for_update=True)
        if profile is None:
            raise profile_not_found()
        return profile

    def _subjects_for(self, data: TutorProfileUpsertRequest) -> list[Subject]:
        requested = data.subjectIds or []
        return resolve_subjects(self.subjects.find_by_ids(requested), requested)

    def _signed_urls(self, profile_id: UUID, file_refs: dict[UUID, str]) -> dict[str, str]:
        if not file_refs:
            return {}
        try:
            return self.storage.create_signed_urls(list(file_refs.values()), SIGNED_URL_TTL_SECONDS)
        except FileStorageError:
            logger.warning("Không tạo được URL ký cho minh chứng của hồ sơ %s", profile_id)
            return {}
