from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.core.constants import ROLE_TUTOR
from app.core.file_storage import FileStorage, get_file_storage
from app.core.file_validation import MAX_EVIDENCE_BYTES, IncomingFile
from app.db.session import get_db
from app.repositories.tutor_profiles import TutorProfileRepository
from app.schemas.auth import CurrentUserResponse
from app.schemas.common import ApiResponse
from app.schemas.tutor_profiles import TutorProfileEvidenceResponse
from app.services.tutor_profile_evidences import TutorProfileEvidenceService

router = APIRouter(prefix="/api/tutor-profiles", tags=["TutorProfiles"])

TutorUser = Annotated[CurrentUserResponse, Depends(require_roles(ROLE_TUTOR))]


def get_evidence_service(
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[FileStorage, Depends(get_file_storage)],
) -> TutorProfileEvidenceService:
    return TutorProfileEvidenceService(TutorProfileRepository(db), storage)


Service = Annotated[TutorProfileEvidenceService, Depends(get_evidence_service)]
EvidenceList = ApiResponse[list[TutorProfileEvidenceResponse]]


def _read_capped(upload: UploadFile) -> IncomingFile:
    return IncomingFile(
        file_name=upload.filename or "", data=upload.file.read(MAX_EVIDENCE_BYTES + 1)
    )


@router.post(
    "/{profile_id}/evidences", status_code=status.HTTP_201_CREATED, response_model=EvidenceList
)
def upload_evidences(
    profile_id: UUID,
    current_user: TutorUser,
    service: Service,
    files: Annotated[list[UploadFile] | None, File()] = None,
) -> EvidenceList:
    incoming = [_read_capped(upload) for upload in files or []]
    return EvidenceList.ok(service.upload(current_user.userId, profile_id, incoming))


@router.delete("/{profile_id}/evidences/{evidence_id}", response_model=ApiResponse[None])
def remove_evidence(
    profile_id: UUID, evidence_id: UUID, current_user: TutorUser, service: Service
) -> ApiResponse[None]:
    service.remove(current_user.userId, profile_id, evidence_id)
    return ApiResponse[None].ok(None, message="Đã gỡ minh chứng.")
