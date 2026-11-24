from collections.abc import Mapping
from uuid import UUID

from app.core.clock import as_utc, as_utc_or_none
from app.db.models import TutorProfile, TutorProfileEvidence
from app.schemas.subjects import SubjectResponse
from app.schemas.tutor_profiles import (
    TutorProfileDetailResponse,
    TutorProfileEvidenceResponse,
    TutorProfileResponse,
)


def to_evidence_response(
    evidence: TutorProfileEvidence, url: str | None = None
) -> TutorProfileEvidenceResponse:
    return TutorProfileEvidenceResponse(
        id=evidence.id,
        fileName=evidence.file_name,
        contentType=evidence.content_type,
        sizeBytes=evidence.size_bytes,
        uploadedAtUtc=as_utc(evidence.created_at),
        url=url,
    )


def _profile_fields(profile: TutorProfile) -> dict[str, object]:
    return {
        "id": profile.id,
        "title": profile.title,
        "subjects": [SubjectResponse(id=s.id, name=s.name) for s in profile.subjects],
        "educationLevel": profile.education_level,
        "teachingMode": profile.teaching_mode,
        "province": profile.province,
        "teachingWards": list(profile.teaching_wards),
        "expectedFeePerSession": profile.expected_fee_per_session,
        "description": profile.description,
        "status": profile.status,
        "availability": profile.availability,
        "isDefault": profile.is_default,
        "rejectReason": profile.reject_reason,
        "evidenceCount": len(profile.evidences),
        "submittedAtUtc": as_utc_or_none(profile.submitted_at),
        "createdAtUtc": as_utc(profile.created_at),
        "updatedAtUtc": as_utc(profile.updated_at),
    }


def to_profile_response(profile: TutorProfile) -> TutorProfileResponse:
    return TutorProfileResponse.model_validate(_profile_fields(profile))


def attach_evidence_urls(
    detail: TutorProfileDetailResponse,
    file_refs: Mapping[UUID, str],
    signed_urls: Mapping[str, str],
) -> TutorProfileDetailResponse:
    evidences = [
        evidence.model_copy(update={"url": signed_urls.get(file_refs.get(evidence.id, ""))})
        for evidence in detail.evidences
    ]
    return detail.model_copy(update={"evidences": evidences})


def to_profile_detail(
    profile: TutorProfile, signed_urls: Mapping[str, str]
) -> TutorProfileDetailResponse:
    evidences = [
        to_evidence_response(evidence, signed_urls.get(evidence.file_ref))
        for evidence in profile.evidences
    ]
    return TutorProfileDetailResponse.model_validate(
        {**_profile_fields(profile), "evidences": evidences}
    )
