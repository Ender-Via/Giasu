from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, joinedload

from app.core.constants import VerificationStatus
from app.db.models import StudentVerification, Tutor


class StudentVerificationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def lock_tutor(self, tutor_id: UUID) -> Tutor | None:
        statement = (
            select(Tutor)
            .where(Tutor.user_id == tutor_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        return self.db.scalar(statement)

    def get_tutor(self, tutor_id: UUID) -> Tutor | None:
        return self.db.get(Tutor, tutor_id)

    def get_latest_for_tutor(self, tutor_id: UUID) -> StudentVerification | None:
        statement = (
            select(StudentVerification)
            .where(StudentVerification.tutor_id == tutor_id)
            .order_by(StudentVerification.created_at.desc(), StudentVerification.id.desc())
            .limit(1)
        )
        return self.db.scalar(statement)

    def has_pending_or_verified(self, tutor_id: UUID) -> bool:
        statement = (
            select(StudentVerification.id)
            .where(
                StudentVerification.tutor_id == tutor_id,
                StudentVerification.status.in_(
                    (VerificationStatus.PENDING, VerificationStatus.VERIFIED)
                ),
            )
            .limit(1)
        )
        return self.db.scalar(statement) is not None

    def list_for_admin(
        self,
        *,
        status: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[StudentVerification], int]:
        filters = [StudentVerification.status == status] if status else []
        total = int(
            self.db.scalar(
                select(func.count()).select_from(StudentVerification).where(*filters)
            )
            or 0
        )
        if status == VerificationStatus.PENDING:
            ordering = (StudentVerification.created_at.asc(), StudentVerification.id.asc())
        elif status in (VerificationStatus.VERIFIED, VerificationStatus.REJECTED):
            ordering = (StudentVerification.reviewed_at.desc(), StudentVerification.id.desc())
        else:
            ordering = (StudentVerification.created_at.desc(), StudentVerification.id.desc())

        statement = (
            select(StudentVerification)
            .where(*filters)
            .options(
                joinedload(StudentVerification.tutor).joinedload(Tutor.user),
                joinedload(StudentVerification.reviewer),
            )
            .order_by(*ordering)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(statement)), total

    def get_by_id(self, verification_id: UUID) -> StudentVerification | None:
        statement = (
            select(StudentVerification)
            .where(StudentVerification.id == verification_id)
            .options(
                joinedload(StudentVerification.tutor).joinedload(Tutor.user),
                joinedload(StudentVerification.reviewer),
            )
        )
        return self.db.scalar(statement)

    def transition_from_pending(
        self,
        verification_id: UUID,
        *,
        to_status: str,
        reviewed_by: UUID,
        reviewed_at: datetime,
        reject_reason: str | None = None,
    ) -> bool:
        result = self.db.execute(
            update(StudentVerification)
            .where(
                StudentVerification.id == verification_id,
                StudentVerification.status == VerificationStatus.PENDING,
            )
            .values(
                status=to_status,
                reviewed_by=reviewed_by,
                reviewed_at=reviewed_at,
                reject_reason=reject_reason,
            )
        )
        return result.rowcount > 0

    def update_tutor_verification_status(self, tutor_id: UUID, status: str) -> None:
        self.db.execute(
            update(Tutor).where(Tutor.user_id == tutor_id).values(verification_status=status)
        )

    def add(self, verification: StudentVerification) -> None:
        self.db.add(verification)

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
