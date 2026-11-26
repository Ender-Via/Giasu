from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import AuditLog


class AuditLogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

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
