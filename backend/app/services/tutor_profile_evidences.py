import logging
from uuid import UUID, uuid4

from app.core.clock import utc_now
from app.core.file_storage import FileStorage, FileStorageError
from app.core.file_validation import (
    STORAGE_EXTENSIONS,
    IncomingFile,
    ValidatedFile,
    validate_evidence_file,
)
from app.db.models import TutorProfile, TutorProfileEvidence
from app.repositories.tutor_profiles import TutorProfileRepository
from app.schemas.tutor_profiles import TutorProfileEvidenceResponse
from app.services.errors import ConflictError, InvalidInputError, NotFoundError
from app.services.tutor_profile_mapping import to_evidence_response
from app.services.tutor_profile_rules import (
    MAX_EVIDENCES_PER_PROFILE,
    ensure_evidence_editable,
    profile_not_found,
)

logger = logging.getLogger(__name__)

MSG_FILE_COUNT = "Chọn từ 1 đến 5 tệp minh chứng."
MSG_EVIDENCE_NOT_FOUND = "Không tìm thấy minh chứng."


def _capacity_error(remaining: int) -> ConflictError:
    return ConflictError(
        f"Mỗi hồ sơ tối đa {MAX_EVIDENCES_PER_PROFILE} minh chứng; "
        f"hồ sơ này chỉ thêm được {max(remaining, 0)} tệp nữa."
    )


def validate_upload(files: list[IncomingFile]) -> list[ValidatedFile]:
    if not files:
        raise InvalidInputError(errors=[MSG_FILE_COUNT])
    if len(files) > MAX_EVIDENCES_PER_PROFILE:
        raise _capacity_error(MAX_EVIDENCES_PER_PROFILE)

    valid: list[ValidatedFile] = []
    errors: list[str] = []
    for incoming in files:
        validated, error = validate_evidence_file(incoming)
        if validated is not None:
            valid.append(validated)
        elif error is not None:
            errors.append(error)
    if errors:
        raise InvalidInputError(errors=errors)
    return valid


class TutorProfileEvidenceService:
    def __init__(self, profiles: TutorProfileRepository, storage: FileStorage) -> None:
        self.profiles = profiles
        self.storage = storage

    def upload(
        self, tutor_id: UUID, profile_id: UUID, files: list[IncomingFile]
    ) -> list[TutorProfileEvidenceResponse]:
        validated = validate_upload(files)
        self._check_can_add(self._profile(tutor_id, profile_id), len(validated))
        self.profiles.rollback()

        uploaded = self._upload_all(profile_id, validated)
        try:
            profile = self._profile(tutor_id, profile_id, for_update=True)
            self._check_can_add(profile, len(uploaded))
            now = utc_now()
            created = [
                TutorProfileEvidence(
                    id=evidence_id,
                    profile_id=profile.id,
                    file_ref=path,
                    file_name=item.file_name,
                    content_type=item.content_type,
                    size_bytes=item.size_bytes,
                    created_at=now,
                )
                for evidence_id, path, item in uploaded
            ]
            for evidence in created:
                self.profiles.add(evidence)
            profile.updated_at = now
            self.profiles.commit()
        except Exception:
            self.profiles.rollback()
            self._delete_quietly([path for _, path, _ in uploaded])
            raise

        return [to_evidence_response(evidence) for evidence in created]

    def _profile(
        self, tutor_id: UUID, profile_id: UUID, *, for_update: bool = False
    ) -> TutorProfile:
        profile = self.profiles.get_for_tutor(tutor_id, profile_id, for_update=for_update)
        if profile is None:
            raise profile_not_found()
        return profile

    @staticmethod
    def _check_can_add(profile: TutorProfile, adding: int) -> None:
        ensure_evidence_editable(profile)
        remaining = MAX_EVIDENCES_PER_PROFILE - len(profile.evidences)
        if adding > remaining:
            raise _capacity_error(remaining)

    def _upload_all(
        self, profile_id: UUID, files: list[ValidatedFile]
    ) -> list[tuple[UUID, str, ValidatedFile]]:
        uploaded: list[tuple[UUID, str, ValidatedFile]] = []
        try:
            for item in files:
                evidence_id = uuid4()
                path = (
                    f"tutor-profiles/{profile_id}/{evidence_id}"
                    f"{STORAGE_EXTENSIONS[item.content_type]}"
                )
                self.storage.upload(path, item.data, item.content_type)
                uploaded.append((evidence_id, path, item))
        except Exception:
            self._delete_quietly([path for _, path, _ in uploaded])
            raise
        return uploaded

    def remove(self, tutor_id: UUID, profile_id: UUID, evidence_id: UUID) -> None:
        profile = self._profile(tutor_id, profile_id, for_update=True)
        ensure_evidence_editable(profile)

        evidence = next((e for e in profile.evidences if e.id == evidence_id), None)
        if evidence is None:
            raise NotFoundError(MSG_EVIDENCE_NOT_FOUND)

        file_ref = evidence.file_ref
        self.profiles.delete(evidence)
        profile.updated_at = utc_now()
        self.profiles.commit()
        self._delete_quietly([file_ref])

    def _delete_quietly(self, paths: list[str]) -> None:
        if not paths:
            return
        try:
            self.storage.delete(paths)
        except FileStorageError:
            logger.warning("Không xóa được %d tệp trên Storage, cần dọn tay", len(paths))
