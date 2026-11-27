from contextlib import AbstractContextManager
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, SessionTransaction

from app.db.models import AuditLog


class AuditLogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def flush(self) -> None:
        self.db.flush()

    def begin_nested(self) -> AbstractContextManager[SessionTransaction]:
        return self.db.begin_nested()

    def record_transition(
        self,
        *,
        actor_id: UUID,
        entity: str,
        entity_id: UUID,
        action: str,
        from_status: str | None,
        to_status: str,
        created_at: datetime,
    ) -> None:
        self.db.add(
            AuditLog(
                actor_id=actor_id,
                entity=entity,
                entity_id=entity_id,
                action=action,
                from_status=from_status,
                to_status=to_status,
                created_at=created_at,
            )
        )

    def list_for_entity(self, entity: str, entity_id: UUID) -> list[AuditLog]:
        statement = (
            select(AuditLog)
            .where(AuditLog.entity == entity, AuditLog.entity_id == entity_id)
            .order_by(AuditLog.created_at.asc(), AuditLog.id.asc())
        )
        return list(self.db.scalars(statement))
