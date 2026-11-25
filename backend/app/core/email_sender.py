import logging
from functools import lru_cache
from typing import Protocol
from uuid import UUID

logger = logging.getLogger(__name__)


class EmailSender(Protocol):
    def send(
        self,
        *,
        recipient_id: UUID,
        recipient_email: str,
        notification_type: str,
        title: str,
        message: str,
        link: str | None = None,
    ) -> None: ...


class LoggingEmailSender:
    """Bản MVP chỉ ghi log thay cho gửi email thật (D13)."""

    def send(
        self,
        *,
        recipient_id: UUID,
        recipient_email: str,
        notification_type: str,
        title: str,
        message: str,
        link: str | None = None,
    ) -> None:
        logger.info(
            "Gửi email [%s] tới %s (user=%s): %s | %s (link=%s)",
            notification_type,
            recipient_email,
            recipient_id,
            title,
            message,
            link or "",
        )


@lru_cache
def get_email_sender() -> EmailSender:
    return LoggingEmailSender()
