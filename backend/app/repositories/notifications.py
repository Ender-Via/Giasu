from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.db.models import Notification, NotificationPreference, User


class NotificationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_user(
        self,
        recipient_id: UUID,
        *,
        unread_only: bool,
        page: int,
        page_size: int,
    ) -> tuple[list[Notification], int]:
        filters = [Notification.recipient_id == recipient_id]
        if unread_only:
            filters.append(Notification.is_read.is_(False))

        total = int(
            self.db.scalar(select(func.count()).select_from(Notification).where(*filters)) or 0
        )
        statement = (
            select(Notification)
            .where(*filters)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(statement)), total

    def count_unread(self, recipient_id: UUID) -> int:
        statement = (
            select(func.count())
            .select_from(Notification)
            .where(Notification.recipient_id == recipient_id, Notification.is_read.is_(False))
        )
        return int(self.db.scalar(statement) or 0)

    def mark_read(self, recipient_id: UUID, notification_id: UUID) -> bool:
        result = self.db.execute(
            update(Notification)
            .where(Notification.id == notification_id, Notification.recipient_id == recipient_id)
            .values(is_read=True)
        )
        return result.rowcount > 0

    def mark_all_read(self, recipient_id: UUID) -> None:
        self.db.execute(
            update(Notification)
            .where(Notification.recipient_id == recipient_id, Notification.is_read.is_(False))
            .values(is_read=True)
        )

    def list_preferences(self, user_id: UUID) -> dict[str, bool]:
        statement = select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        return {pref.type: pref.email_enabled for pref in self.db.scalars(statement)}

    def upsert_preferences(self, user_id: UUID, items: Sequence[tuple[str, bool]]) -> None:
        existing = {
            pref.type: pref
            for pref in self.db.scalars(
                select(NotificationPreference).where(NotificationPreference.user_id == user_id)
            )
        }
        for notification_type, email_enabled in items:
            row = existing.get(notification_type)
            if row is not None:
                row.email_enabled = email_enabled
            else:
                self.db.add(
                    NotificationPreference(
                        user_id=user_id,
                        type=notification_type,
                        email_enabled=email_enabled,
                    )
                )

    def list_active_recipients(self, recipient_ids: Sequence[UUID]) -> list[User]:
        if not recipient_ids:
            return []
        statement = select(User).where(User.id.in_(recipient_ids), User.is_active.is_(True))
        return list(self.db.scalars(statement))

    def list_active_admins(self) -> list[User]:
        statement = select(User).where(User.role_id == 1, User.is_active.is_(True))
        return list(self.db.scalars(statement))

    def list_email_disabled_users(
        self, user_ids: Sequence[UUID], notification_type: str
    ) -> set[UUID]:
        if not user_ids:
            return set()
        statement = select(NotificationPreference.user_id).where(
            NotificationPreference.user_id.in_(user_ids),
            NotificationPreference.type == notification_type,
            NotificationPreference.email_enabled.is_(False),
        )
        return set(self.db.scalars(statement))

    def add(self, notification: Notification) -> None:
        self.db.add(notification)

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
