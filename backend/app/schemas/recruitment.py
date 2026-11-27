import unicodedata
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
    StrictInt,
    ValidationError,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    field_validator,
)

from app.core.constants import EDUCATION_LEVELS, TeachingMode
from app.core.provinces import normalize_province
from app.core.recruitment_status import TutorRequestStatusName

FIELD_MESSAGES = {
    "fullName": "Họ tên phải từ 2 đến 100 ký tự.",
    "gradeLevel": "Lớp phải là số nguyên từ 1 đến 12.",
    "studentId": "Vui lòng chọn học sinh hợp lệ.",
    "subjectId": "Vui lòng chọn môn học trong danh mục.",
    "title": "Tiêu đề tin phải là văn bản tối đa 150 ký tự.",
    "sessionsPerWeek": "Số buổi mỗi tuần phải là số nguyên từ 1 đến 7.",
    "minFee": "Học phí tối thiểu phải là số nguyên từ 50.000 đến 2.000.000 đồng.",
    "maxFee": "Học phí tối đa phải là số nguyên từ 50.000 đến 2.000.000 đồng.",
    "requirements": "Yêu cầu với gia sư phải từ 1 đến 2000 ký tự.",
}


def clean_text(value: object) -> str | None:
    if not isinstance(value, str) or "\x00" in value:
        return None
    return unicodedata.normalize("NFC", value).strip() or None


class RecruitmentInput(BaseModel):
    @field_validator("*", mode="wrap")
    @classmethod
    def explain_field_error(
        cls, value: object, handler: ValidatorFunctionWrapHandler, info: ValidationInfo
    ) -> object:
        try:
            return handler(value)
        except ValidationError as exc:
            message = FIELD_MESSAGES.get(info.field_name)
            if message and exc.errors(include_url=False)[0]["type"] != "value_error":
                raise ValueError(message) from exc
            raise


class StudentUpsertRequest(RecruitmentInput):
    fullName: Annotated[str, BeforeValidator(clean_text), Field(min_length=2, max_length=100)]
    gradeLevel: Annotated[StrictInt, Field(ge=1, le=12)]


Fee = Annotated[StrictInt, Field(ge=50_000, le=2_000_000)]


class TutorRequestUpsertRequest(RecruitmentInput):
    studentId: UUID
    subjectId: Annotated[StrictInt, Field(ge=1, le=32_767)]
    title: Annotated[str, Field(max_length=150)] | None = None
    educationLevel: str
    teachingMode: str
    province: str | None = Field(default=None, validate_default=True)
    ward: str | None = Field(default=None, validate_default=True)
    address: str | None = None
    sessionsPerWeek: Annotated[StrictInt, Field(ge=1, le=7)]
    minFee: Fee
    maxFee: Fee
    requirements: Annotated[str, BeforeValidator(clean_text), Field(min_length=1, max_length=2000)]

    @field_validator("title", mode="before")
    @classmethod
    def check_title(cls, value: object) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str) or "\x00" in value:
            raise ValueError(FIELD_MESSAGES["title"])
        return clean_text(value)

    @field_validator("educationLevel", mode="before")
    @classmethod
    def check_education_level(cls, value: object) -> str:
        if value not in EDUCATION_LEVELS:
            raise ValueError("Vui lòng chọn cấp học hợp lệ.")
        return value

    @field_validator("teachingMode", mode="before")
    @classmethod
    def check_teaching_mode(cls, value: object) -> str:
        if value not in TeachingMode.ALL:
            raise ValueError("Vui lòng chọn hình thức dạy hợp lệ.")
        return value

    @field_validator("province", mode="before")
    @classmethod
    def check_province(cls, value: object, info: ValidationInfo) -> str | None:
        if info.data.get("teachingMode") in (None, TeachingMode.ONLINE):
            return None
        province = normalize_province(value) if isinstance(value, str) else None
        if province is None:
            raise ValueError("Vui lòng chọn tỉnh/thành trong danh mục.")
        return province

    @field_validator("ward", mode="before")
    @classmethod
    def check_ward(cls, value: object, info: ValidationInfo) -> str | None:
        if info.data.get("teachingMode") in (None, TeachingMode.ONLINE):
            return None
        ward = clean_text(value)
        if ward is None or len(ward) > 100:
            raise ValueError("Phường/xã phải từ 1 đến 100 ký tự.")
        return ward

    @field_validator("address", mode="before")
    @classmethod
    def check_address(cls, value: object, info: ValidationInfo) -> str | None:
        if value is None or info.data.get("teachingMode") in (None, TeachingMode.ONLINE):
            return None
        if not isinstance(value, str) or "\x00" in value:
            raise ValueError("Địa chỉ phải là văn bản hợp lệ.")
        address = clean_text(value)
        if address and len(address) > 200:
            raise ValueError("Địa chỉ không quá 200 ký tự.")
        return address

    @field_validator("maxFee")
    @classmethod
    def check_fee_range(cls, value: int, info: ValidationInfo) -> int:
        min_fee = info.data.get("minFee")
        if min_fee is not None and min_fee > value:
            raise ValueError("Học phí tối thiểu không được lớn hơn học phí tối đa.")
        return value


class StudentResponse(BaseModel):
    id: UUID
    fullName: str
    gradeLevel: int
    createdAtUtc: datetime


class TutorRequestPublicResponse(BaseModel):
    id: UUID
    title: str | None
    subjectName: str
    studentGradeLevel: int
    educationLevel: str
    teachingMode: str
    province: str | None
    ward: str | None
    sessionsPerWeek: int
    minFee: int
    maxFee: int
    requirements: str
    approvedAtUtc: datetime | None
    hasOpenApplication: bool


class TutorRequestResponse(BaseModel):
    id: UUID
    title: str | None
    studentId: UUID
    studentName: str
    studentGradeLevel: int
    subjectId: int
    subjectName: str
    educationLevel: str
    teachingMode: str
    province: str | None
    ward: str | None
    address: str | None
    sessionsPerWeek: int
    minFee: int
    maxFee: int
    requirements: str
    status: TutorRequestStatusName
    openApplicationCount: int
    rejectReason: str | None
    expiresAtUtc: datetime | None
    submittedAtUtc: datetime
    reviewedAtUtc: datetime | None
    createdAtUtc: datetime
    updatedAtUtc: datetime


class RequestParentResponse(BaseModel):
    id: UUID
    fullName: str
    email: str
    phone: str


class TutorRequestAdminResponse(TutorRequestResponse):
    reviewedByName: str | None = None
    parent: RequestParentResponse


class TutorRequestPageResponse(BaseModel):
    items: list[TutorRequestResponse]
    page: int
    pageSize: int
    totalCount: int
