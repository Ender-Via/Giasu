import re
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, SecretStr, field_validator

RoleName = Literal["Admin", "Tutor", "Parent"]
RegistrationRole = Literal["Tutor", "Parent"]


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_default=True)

    role: RegistrationRole = None  # type: ignore[assignment]
    fullName: str = None  # type: ignore[assignment]
    phone: str = None  # type: ignore[assignment]
    email: str = None  # type: ignore[assignment]
    password: SecretStr = None  # type: ignore[assignment]
    acceptTerms: bool = None  # type: ignore[assignment]

    @field_validator("role", mode="plain")
    @classmethod
    def validate_role(cls, value: object) -> str:
        if value not in ("Tutor", "Parent"):
            raise ValueError("Vui lòng chọn vai trò Gia sư hoặc Phụ huynh.")
        return str(value)

    @field_validator("fullName", mode="before")
    @classmethod
    def validate_full_name(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("Họ tên từ 2 đến 100 ký tự.")
        normalized = " ".join(value.split())
        if not 2 <= len(normalized) <= 100:
            raise ValueError("Họ tên từ 2 đến 100 ký tự.")
        return normalized

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("Số điện thoại gồm 10 chữ số, bắt đầu bằng 0.")
        normalized = value.strip()
        if re.fullmatch(r"0[0-9]{9}", normalized) is None:
            raise ValueError("Số điện thoại gồm 10 chữ số, bắt đầu bằng 0.")
        return normalized

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("Email không đúng định dạng.")
        normalized = value.strip().lower()
        if len(normalized) > 254 or re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized) is None:
            raise ValueError("Email không đúng định dạng.")
        return normalized

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, value: object) -> SecretStr:
        if isinstance(value, SecretStr):
            password = value.get_secret_value()
        elif isinstance(value, str):
            password = value
        else:
            raise ValueError("Mật khẩu từ 8 đến 128 ký tự, có cả chữ và số.")
        if (
            not 8 <= len(password) <= 128
            or not any(char.isalpha() for char in password)
            or not any(char.isdigit() for char in password)
        ):
            raise ValueError("Mật khẩu từ 8 đến 128 ký tự, có cả chữ và số.")
        return value if isinstance(value, SecretStr) else SecretStr(password)

    @field_validator("acceptTerms", mode="before")
    @classmethod
    def validate_accept_terms(cls, value: object) -> bool:
        if value is not True:
            raise ValueError("Bạn cần đồng ý quy chế để tiếp tục.")
        return True


class CurrentUserResponse(BaseModel):
    userId: UUID
    fullName: str
    role: RoleName
