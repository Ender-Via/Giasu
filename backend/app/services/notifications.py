from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID, uuid4

from app.core.clock import as_utc, utc_now
from app.core.constants import NotificationType
from app.core.email_sender import EmailSender
from app.db.models import Notification, User
from app.repositories.notifications import NotificationRepository
from app.schemas.auth import RoleName
from app.schemas.notifications import (
    MSG_INVALID_TYPE,
    NotificationPageResponse,
    NotificationPreferenceItem,
    NotificationPreferencesResponse,
    NotificationResponse,
)
from app.services.errors import InvalidInputError, NotFoundError

MSG_NOTIFICATION_NOT_FOUND = "Không tìm thấy thông báo."
MSG_DUPLICATE_TYPE = "Loại thông báo bị lặp trong danh sách."
MSG_INVALID_LINK = "Đường dẫn thông báo phải là đường dẫn tương đối."


@dataclass(frozen=True)
class PendingEmail:
    recipient_id: UUID
    recipient_email: str
    notification_type: str
    title: str
    message: str
    link: str | None = None


def _to_response(item: Notification) -> NotificationResponse:
    return NotificationResponse(
        id=item.id,
        type=item.type,
        title=item.title,
        message=item.message,
        link=item.link,
        isRead=item.is_read,
        createdAtUtc=as_utc(item.created_at),
    )


def _validate_link(link: str | None) -> str | None:
    if link is None:
        return None
    if not link.startswith("/") or link.startswith("//"):
        raise InvalidInputError(errors=[MSG_INVALID_LINK])
    return link


class NotificationService:
    def __init__(self, notifications: NotificationRepository, email_sender: EmailSender) -> None:
        self.notifications = notifications
        self.email_sender = email_sender

    def list_mine(
        self, recipient_id: UUID, *, unread_only: bool, page: int, page_size: int
    ) -> NotificationPageResponse:
        items, total_count = self.notifications.list_for_user(
            recipient_id,
            unread_only=unread_only,
            page=page,
            page_size=page_size,
        )
        return NotificationPageResponse(
            items=[_to_response(item) for item in items],
            page=page,
            pageSize=page_size,
            totalCount=total_count,
        )

    def get_unread_count(self, recipient_id: UUID) -> int:
        return self.notifications.count_unread(recipient_id)

    def mark_read(self, recipient_id: UUID, notification_id: UUID) -> None:
        if not self.notifications.mark_read(recipient_id, notification_id):
            raise NotFoundError(MSG_NOTIFICATION_NOT_FOUND)
        self.notifications.commit()

    def mark_all_read(self, recipient_id: UUID) -> None:
        self.notifications.mark_all_read(recipient_id)
        self.notifications.commit()

    def get_preferences(self, user_id: UUID, role: RoleName) -> NotificationPreferencesResponse:
        stored = self.notifications.list_preferences(user_id)
        allowed_types = NotificationType.BY_ROLE.get(role, ())
        return NotificationPreferencesResponse(
            items=[
                NotificationPreferenceItem(
                    type=notification_type,
                    emailEnabled=stored.get(notification_type, True),
                )
                for notification_type in allowed_types
            ]
        )

    def update_preferences(
        self,
        user_id: UUID,
        role: RoleName,
        items: Sequence[NotificationPreferenceItem],
    ) -> NotificationPreferencesResponse:
        allowed_types = set(NotificationType.BY_ROLE.get(role, ()))
        seen: set[str] = set()
        normalized: list[tuple[str, bool]] = []
        for item in items:
            notification_type = item.type or ""
            if notification_type not in allowed_types:
                raise InvalidInputError(errors=[MSG_INVALID_TYPE])
            if notification_type in seen:
                raise InvalidInputError(errors=[MSG_DUPLICATE_TYPE])
            seen.add(notification_type)
            normalized.append((notification_type, bool(item.emailEnabled)))

        self.notifications.upsert_preferences(user_id, normalized)
        self.notifications.commit()
        return self.get_preferences(user_id, role)

    def queue_many(
        self,
        recipient_ids: Sequence[UUID],
        notification_type: str,
        title: str,
        message: str,
        link: str | None = None,
    ) -> list[PendingEmail]:
        recipients = self.notifications.list_active_recipients(list(dict.fromkeys(recipient_ids)))
        return self._queue_for_users(recipients, notification_type, title, message, link)

    def queue_for_active_admins(
        self,
        notification_type: str,
        title: str,
        message: str,
        link: str | None = None,
    ) -> list[PendingEmail]:
        admins = self.notifications.list_active_admins()
        return self._queue_for_users(admins, notification_type, title, message, link)

    def notify(
        self,
        recipient_id: UUID,
        notification_type: str,
        title: str,
        message: str,
        link: str | None = None,
    ) -> None:
        self.notify_many([recipient_id], notification_type, title, message, link)

    def notify_many(
        self,
        recipient_ids: Sequence[UUID],
        notification_type: str,
        title: str,
        message: str,
        link: str | None = None,
    ) -> None:
        pending = self.queue_many(recipient_ids, notification_type, title, message, link)
        self.notifications.commit()
        self.dispatch_emails(pending)

    def notify_active_admins(
        self,
        notification_type: str,
        title: str,
        message: str,
        link: str | None = None,
    ) -> None:
        pending = self.queue_for_active_admins(notification_type, title, message, link)
        self.notifications.commit()
        self.dispatch_emails(pending)

    def dispatch_emails(self, pending: Sequence[PendingEmail]) -> None:
        for item in pending:
            self.email_sender.send(
                recipient_id=item.recipient_id,
                recipient_email=item.recipient_email,
                notification_type=item.notification_type,
                title=item.title,
                message=item.message,
                link=item.link,
            )

    def _queue_for_users(
        self,
        users: Sequence[User],
        notification_type: str,
        title: str,
        message: str,
        link: str | None,
    ) -> list[PendingEmail]:
        if notification_type not in NotificationType.ALL:
            raise InvalidInputError(errors=[MSG_INVALID_TYPE])
        cleaned_link = _validate_link(link)
        if not users:
            return []

        now = utc_now()
        disabled_ids = self.notifications.list_email_disabled_users(
            [user.id for user in users], notification_type
        )
        pending_emails: list[PendingEmail] = []
        for user in users:
            self.notifications.add(
                Notification(
                    id=uuid4(),
                    recipient_id=user.id,
                    type=notification_type,
                    title=title,
                    message=message,
                    link=cleaned_link,
                    is_read=False,
                    created_at=now,
                )
            )
            if user.id not in disabled_ids:
                pending_emails.append(
                    PendingEmail(
                        recipient_id=user.id,
                        recipient_email=user.login_identifier,
                        notification_type=notification_type,
                        title=title,
                        message=message,
                        link=cleaned_link,
                    )
                )
        return pending_emails
