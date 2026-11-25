import re
import unicodedata
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

MSG_UNIVERSITY = "Tên trường từ 2 đến 150 ký tự."
MSG_STUDENT_CODE = "Mã số sinh viên từ 3 đến 20 ký tự, chỉ gồm chữ và số."
MSG_REJECT_REASON = "Lý do từ chối bắt buộc và không quá 500 ký tự."
MSG_INVALID_STATUS = "Trạng thái xác thực không hợp lệ."

_STUDENT_CODE_RE = re.compile(r"^[A-Za-z0-9]{3,20}$")


def _clean_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = unicodedata.normalize("NFC", value).strip()
    return cleaned or None


def validate_university(value: str | None) -> str | None:
    cleaned = _clean_text(value)
    if cleaned is None or not 2 <= len(cleaned) <= 150:
        return None
    return cleaned


def validate_student_code(value: str | None) -> str | None:
    cleaned = _clean_text(value)
    if cleaned is None or not _STUDENT_CODE_RE.fullmatch(cleaned):
        return None
    return cleaned


class RejectVerificationRequest(BaseModel):
    model_config = ConfigDict(validate_default=True)

    reason: str | None = None

    @field_validator("reason", mode="before")
    @classmethod
    def check_reason(cls, value: Any) -> str:
        cleaned = _clean_text(value)
        if cleaned is None or len(cleaned) > 500:
            raise ValueError(MSG_REJECT_REASON)
        return cleaned


class TutorVerificationResponse(BaseModel):
    id: UUID
    university: str
    studentCode: str
    status: str
    rejectReason: str | None
    createdAtUtc: datetime
    reviewedAtUtc: datetime | None


class AdminVerificationListItemResponse(BaseModel):
    id: UUID
    tutorId: UUID
    tutorName: str
    tutorEmail: str
    university: str
    studentCode: str
    status: str
    rejectReason: str | None
    reviewedByName: str | None
    reviewedAtUtc: datetime | None
    createdAtUtc: datetime


class AdminVerificationPageResponse(BaseModel):
    items: list[AdminVerificationListItemResponse]
    page: int
    pageSize: int
    totalCount: int


class AdminVerificationDetailResponse(AdminVerificationListItemResponse):
    tutorPhone: str
    evidenceUrl: str | None
