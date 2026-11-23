import unicodedata
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator

from app.core.constants import EDUCATION_LEVELS, Availability, TeachingMode
from app.core.provinces import normalize_province
from app.schemas.subjects import SubjectResponse

MSG_TITLE = "Tiêu đề từ 10 đến 150 ký tự"
MSG_SUBJECTS = "Chọn từ 1 đến 5 môn"
MSG_EDUCATION_LEVEL = "Vui lòng chọn cấp học"
MSG_TEACHING_MODE = "Vui lòng chọn hình thức dạy"
MSG_PROVINCE = "Vui lòng chọn tỉnh/thành"
MSG_PROVINCE_INVALID = "Tỉnh/thành không hợp lệ"
MSG_WARDS_REQUIRED = "Nhập ít nhất một phường/xã"
MSG_WARDS_MAX = "Nhập tối đa 5 phường/xã"
MSG_WARD_LENGTH = "Mỗi phường/xã không quá 100 ký tự"
MSG_FEE = "Học phí từ 50.000 đến 2.000.000 đồng, làm tròn đến nghìn"
MSG_DESCRIPTION = "Giới thiệu không quá 2000 ký tự"
MSG_AVAILABILITY = "Trạng thái nhận dạy không hợp lệ."

MAX_SUBJECTS = 5
MAX_SUBJECT_ID = 32_767
MAX_WARDS = 5
MAX_WARD_LENGTH = 100
MIN_FEE, MAX_FEE, FEE_STEP = 50_000, 2_000_000, 1_000


def _clean(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = unicodedata.normalize("NFC", value).strip()
    return cleaned or None


class TutorProfileUpsertRequest(BaseModel):
    model_config = ConfigDict(validate_default=True)

    title: str | None = None
    subjectIds: list[int] | None = None
    educationLevel: str | None = None
    teachingMode: str | None = None
    province: str | None = None
    teachingWards: list[str] | None = None
    expectedFeePerSession: int | None = None
    description: str | None = None

    @field_validator("title", mode="before")
    @classmethod
    def check_title(cls, value: Any) -> str:
        title = _clean(value)
        if title is None or not 10 <= len(title) <= 150:
            raise ValueError(MSG_TITLE)
        return title

    @field_validator("subjectIds", mode="before")
    @classmethod
    def check_subjects(cls, value: Any) -> list[int]:
        if not isinstance(value, list) or any(
            isinstance(item, bool) or not isinstance(item, int) or not 1 <= item <= MAX_SUBJECT_ID
            for item in value
        ):
            raise ValueError(MSG_SUBJECTS)
        unique_ids = list(dict.fromkeys(value))
        if not 1 <= len(unique_ids) <= MAX_SUBJECTS:
            raise ValueError(MSG_SUBJECTS)
        return unique_ids

    @field_validator("educationLevel", mode="before")
    @classmethod
    def check_education_level(cls, value: Any) -> str:
        if value not in EDUCATION_LEVELS:
            raise ValueError(MSG_EDUCATION_LEVEL)
        return value

    @field_validator("teachingMode", mode="before")
    @classmethod
    def check_teaching_mode(cls, value: Any) -> str:
        if value not in TeachingMode.ALL:
            raise ValueError(MSG_TEACHING_MODE)
        return value

    @field_validator("province", mode="before")
    @classmethod
    def check_province(cls, value: Any) -> str:
        cleaned = _clean(value)
        if cleaned is None:
            raise ValueError(MSG_PROVINCE)
        province = normalize_province(cleaned)
        if province is None:
            raise ValueError(MSG_PROVINCE_INVALID)
        return province

    @field_validator("teachingWards", mode="before")
    @classmethod
    def check_wards(cls, value: Any, info: ValidationInfo) -> list[str]:
        mode = info.data.get("teachingMode")
        if mode == TeachingMode.ONLINE:
            return []
        if value is None:
            value = []
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise ValueError(MSG_WARDS_REQUIRED)
        wards = list(dict.fromkeys(ward for ward in map(_clean, value) if ward))
        if any(len(ward) > MAX_WARD_LENGTH for ward in wards):
            raise ValueError(MSG_WARD_LENGTH)
        if len(wards) > MAX_WARDS:
            raise ValueError(MSG_WARDS_MAX)
        if mode is not None and not wards:
            raise ValueError(MSG_WARDS_REQUIRED)
        return wards

    @field_validator("expectedFeePerSession", mode="before")
    @classmethod
    def check_fee(cls, value: Any) -> int:
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not MIN_FEE <= value <= MAX_FEE
            or value % FEE_STEP != 0
        ):
            raise ValueError(MSG_FEE)
        return value

    @field_validator("description", mode="before")
    @classmethod
    def check_description(cls, value: Any) -> str | None:
        if value is not None and not isinstance(value, str):
            raise ValueError(MSG_DESCRIPTION)
        description = _clean(value)
        if description is not None and len(description) > 2000:
            raise ValueError(MSG_DESCRIPTION)
        return description


class AvailabilityRequest(BaseModel):
    model_config = ConfigDict(validate_default=True)

    availability: str | None = None

    @field_validator("availability", mode="before")
    @classmethod
    def check_availability(cls, value: Any) -> str:
        if value not in Availability.ALL:
            raise ValueError(MSG_AVAILABILITY)
        return value


class TutorProfileEvidenceResponse(BaseModel):
    id: UUID
    fileName: str
    contentType: str
    sizeBytes: int
    uploadedAtUtc: datetime
    url: str | None = None


class TutorProfileResponse(BaseModel):
    id: UUID
    title: str
    subjects: list[SubjectResponse]
    educationLevel: str
    teachingMode: str
    province: str
    teachingWards: list[str]
    expectedFeePerSession: int
    description: str | None
    status: str
    availability: str
    isDefault: bool
    rejectReason: str | None
    evidenceCount: int
    submittedAtUtc: datetime | None
    createdAtUtc: datetime
    updatedAtUtc: datetime


class TutorProfileDetailResponse(TutorProfileResponse):
    evidences: list[TutorProfileEvidenceResponse]
