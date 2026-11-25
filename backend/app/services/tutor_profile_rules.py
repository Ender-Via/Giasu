from collections.abc import Sequence
from datetime import datetime
from typing import Final

from app.core.constants import TutorProfileStatus
from app.db.models import Subject, TutorProfile
from app.schemas.tutor_profiles import MSG_SUBJECTS, TutorProfileUpsertRequest
from app.services.errors import ConflictError, InvalidInputError, NotFoundError

MAX_PROFILES_PER_TUTOR: Final = 5
MAX_EVIDENCES_PER_PROFILE: Final = 5

MSG_PROFILE_NOT_FOUND: Final = "Không tìm thấy hồ sơ."
MSG_TUTOR_NOT_FOUND: Final = "Không tìm thấy tài khoản gia sư."
MSG_PROFILE_LIMIT: Final = "Bạn đã có 5 hồ sơ, không tạo thêm được."
MSG_PENDING_LOCKED: Final = "Hồ sơ đang chờ duyệt, chưa sửa được."
MSG_SUBMIT_STATE: Final = "Chỉ gửi duyệt được hồ sơ ở trạng thái Nháp hoặc Bị từ chối."
MSG_EVIDENCE_STATE: Final = (
    "Chỉ thêm hoặc gỡ minh chứng khi hồ sơ ở trạng thái Nháp hoặc Bị từ chối."
)
MSG_SUBJECT_INVALID: Final = "Môn học không hợp lệ."
MSG_NEED_DESCRIPTION: Final = "Hồ sơ cần phần giới thiệu, kinh nghiệm."
MSG_NEED_EVIDENCE: Final = "Hồ sơ cần ít nhất một minh chứng."


def profile_not_found() -> NotFoundError:
    return NotFoundError(MSG_PROFILE_NOT_FOUND)


def ensure_evidence_editable(profile: TutorProfile) -> None:
    if profile.status not in TutorProfileStatus.EDITABLE_EVIDENCE:
        raise ConflictError(MSG_EVIDENCE_STATE)


def resolve_subjects(found: Sequence[Subject], requested_ids: Sequence[int]) -> list[Subject]:
    by_id = {subject.id: subject for subject in found}
    if any(subject_id not in by_id for subject_id in requested_ids):
        raise InvalidInputError(errors=[MSG_SUBJECT_INVALID])
    return sorted((by_id[subject_id] for subject_id in set(requested_ids)), key=lambda s: s.id)


def missing_submission_requirements(profile: TutorProfile) -> list[str]:
    missing: list[str] = []
    if not profile.subjects:
        missing.append(MSG_SUBJECTS)
    if not profile.description:
        missing.append(MSG_NEED_DESCRIPTION)
    if not profile.evidences:
        missing.append(MSG_NEED_EVIDENCE)
    return missing


def content_differs(
    profile: TutorProfile, data: TutorProfileUpsertRequest, subjects: Sequence[Subject]
) -> bool:
    return (
        profile.title != data.title
        or {subject.id for subject in profile.subjects} != {subject.id for subject in subjects}
        or profile.education_level != data.educationLevel
        or profile.teaching_mode != data.teachingMode
        or profile.province != data.province
        or list(profile.teaching_wards) != data.teachingWards
        or profile.expected_fee_per_session != data.expectedFeePerSession
        or profile.description != data.description
    )


def apply_content(
    profile: TutorProfile, data: TutorProfileUpsertRequest, subjects: Sequence[Subject]
) -> None:
    profile.title = data.title
    profile.subjects = list(subjects)
    profile.education_level = data.educationLevel
    profile.teaching_mode = data.teachingMode
    profile.province = data.province
    profile.teaching_wards = list(data.teachingWards or [])
    profile.expected_fee_per_session = data.expectedFeePerSession
    profile.description = data.description


def mark_pending_review(profile: TutorProfile, now: datetime) -> None:
    profile.status = TutorProfileStatus.PENDING_REVIEW
    profile.reject_reason = None
    profile.submitted_at = now
    profile.updated_at = now
