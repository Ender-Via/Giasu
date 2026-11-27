import logging
from datetime import datetime
from uuid import UUID

from app.core.clock import utc_now
from app.db.models import AuditLog
from app.repositories.audit_logs import AuditLogRepository

logger = logging.getLogger(__name__)


class AuditLogService:
    """Dịch vụ nhật ký chuyển trạng thái dùng chung (BR-22, NFR-04).

    Ghi log trong savepoint riêng để lỗi ghi audit_logs không làm gián đoạn luồng nghiệp vụ chính.
    """

    def __init__(self, repository: AuditLogRepository) -> None:
        self.repository = repository

    def record_transition(
        self,
        *,
        actor_id: UUID,
        entity: str,
        entity_id: UUID,
        action: str,
        from_status: str | None,
        to_status: str,
        created_at: datetime | None = None,
    ) -> bool:
        timestamp = created_at or utc_now()
        # Flush thay đổi nghiệp vụ trước khi mở savepoint để lỗi nghiệp vụ không bị nuốt.
        self.repository.flush()
        try:
            with self.repository.begin_nested():
                self.repository.record_transition(
                    actor_id=actor_id,
                    entity=entity,
                    entity_id=entity_id,
                    action=action,
                    from_status=from_status,
                    to_status=to_status,
                    created_at=timestamp,
                )
                self.repository.flush()
            return True
        except Exception:
            logger.exception(
                "Không ghi được audit_logs cho %s(%s) action=%s (%s -> %s)",
                entity,
                entity_id,
                action,
                from_status,
                to_status,
            )
            return False

    def list_for_entity(self, entity: str, entity_id: UUID) -> list[AuditLog]:
        return self.repository.list_for_entity(entity, entity_id)


def as_audit_service(audit: AuditLogService | AuditLogRepository) -> AuditLogService:
    if isinstance(audit, AuditLogService):
        return audit
    return AuditLogService(audit)
