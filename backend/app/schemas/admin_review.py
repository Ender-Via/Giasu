import unicodedata
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.recruitment import TutorRequestAdminResponse
from app.schemas.tutor_profiles import TutorProfileDetailResponse, TutorProfileResponse

MSG_REJECT_REASON = "Lý do từ chối bắt buộc và không quá 500 ký tự."
MSG_INVALID_PROFILE_STATUS = "Trạng thái hồ sơ không hợp lệ."
MSG_INVALID_REQUEST_STATUS = "Trạng thái tin tìm gia sư không hợp lệ."


def _clean_reason(value: Any) -> str | None:
    if not isinstance(value, str) or "\x00" in value:
        return None
    return unicodedata.normalize("NFC", value).strip() or None


class RejectModerationRequest(BaseModel):
    model_config = ConfigDict(validate_default=True)

    reason: str | None = None

    @field_validator("reason", mode="before")
    @classmethod
    def check_reason(cls, value: Any) -> str:
        cleaned = _clean_reason(value)
        if cleaned is None or len(cleaned) > 500:
            raise ValueError(MSG_REJECT_REASON)
        return cleaned


class AdminTutorSummaryResponse(BaseModel):
    id: UUID
    fullName: str
    email: str
    phone: str
    verificationStatus: str


class AdminTutorProfileListItemResponse(TutorProfileResponse):
    reviewedByName: str | None
    reviewedAtUtc: datetime | None
    tutor: AdminTutorSummaryResponse


class AdminTutorProfileDetailResponse(TutorProfileDetailResponse):
    reviewedByName: str | None
    reviewedAtUtc: datetime | None
    tutor: AdminTutorSummaryResponse


class AdminTutorProfilePageResponse(BaseModel):
    items: list[AdminTutorProfileListItemResponse]
    page: int
    pageSize: int
    totalCount: int


class AdminTutorRequestPageResponse(BaseModel):
    items: list[TutorRequestAdminResponse]
    page: int
    pageSize: int
    totalCount: int
