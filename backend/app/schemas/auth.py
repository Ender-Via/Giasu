import re
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, SecretStr, field_validator

RoleName = Literal["Admin", "Tutor", "Parent"]
RegistrationRole = Literal["Tutor", "Parent"]


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: RegistrationRole
    fullName: str
    phone: str
    email: str
    password: SecretStr
    acceptTerms: bool

    @field_validator("fullName")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not 2 <= len(normalized) <= 100:
            raise ValueError("Họ tên từ 2 đến 100 ký tự.")
        return normalized

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        normalized = value.strip()
        if re.fullmatch(r"0\d{9}", normalized) is None:
            raise ValueError("Số điện thoại gồm 10 chữ số, bắt đầu bằng 0.")
        return normalized

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if len(normalized) > 254 or re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized) is None:
            raise ValueError("Email không đúng định dạng.")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: SecretStr) -> SecretStr:
        password = value.get_secret_value()
        if not 8 <= len(password) <= 128 or not any(char.isalpha() for char in password) or not any(
            char.isdigit() for char in password
        ):
            raise ValueError("Mật khẩu từ 8 đến 128 ký tự, có cả chữ và số.")
        return value

    @field_validator("acceptTerms")
    @classmethod
    def validate_accept_terms(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Bạn cần đồng ý quy chế để tiếp tục.")
        return value


class CurrentUserResponse(BaseModel):
    userId: UUID
    fullName: str
    role: RoleName
