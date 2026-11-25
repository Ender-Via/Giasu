from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.constants import NotificationType

MSG_INVALID_TYPE = "Loại thông báo không hợp lệ."
MSG_INVALID_EMAIL_ENABLED = "Trạng thái bật email phải là true hoặc false."
MSG_ITEMS_REQUIRED = "Danh sách cấu hình thông báo không hợp lệ."


class NotificationResponse(BaseModel):
    id: UUID
    type: str
    title: str
    message: str
    link: str | None
    isRead: bool
    createdAtUtc: datetime


class NotificationPageResponse(BaseModel):
    items: list[NotificationResponse]
    page: int
    pageSize: int
    totalCount: int


class UnreadCountResponse(BaseModel):
    count: int


class NotificationPreferenceItem(BaseModel):
    model_config = ConfigDict(validate_default=True)

    type: str | None = None
    emailEnabled: bool | None = None

    @field_validator("type", mode="before")
    @classmethod
    def check_type(cls, value: Any) -> str:
        if not isinstance(value, str) or value not in NotificationType.ALL:
            raise ValueError(MSG_INVALID_TYPE)
        return value

    @field_validator("emailEnabled", mode="before")
    @classmethod
    def check_email_enabled(cls, value: Any) -> bool:
        if not isinstance(value, bool):
            raise ValueError(MSG_INVALID_EMAIL_ENABLED)
        return value


class NotificationPreferencesResponse(BaseModel):
    items: list[NotificationPreferenceItem]


class UpdateNotificationPreferencesRequest(BaseModel):
    model_config = ConfigDict(validate_default=True)

    items: list[NotificationPreferenceItem] | None = None

    @field_validator("items", mode="before")
    @classmethod
    def check_items(cls, value: Any) -> Any:
        if not isinstance(value, list) or not value:
            raise ValueError(MSG_ITEMS_REQUIRED)
        return value
