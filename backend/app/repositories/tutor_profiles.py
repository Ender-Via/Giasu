from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, selectinload

from app.db.models import Tutor, TutorProfile, TutorProfileEvidence


class TutorProfileRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def lock_tutor(self, tutor_id: UUID) -> bool:
        statement = (
            select(Tutor.user_id).where(Tutor.user_id == tutor_id).with_for_update(key_share=True)
        )
        return self.db.scalar(statement) is not None

    def count_for_tutor(self, tutor_id: UUID) -> int:
        statement = (
            select(func.count()).select_from(TutorProfile).where(TutorProfile.tutor_id == tutor_id)
        )
        return int(self.db.scalar(statement) or 0)

    def list_for_tutor(self, tutor_id: UUID) -> list[TutorProfile]:
        statement = (
            select(TutorProfile)
            .where(TutorProfile.tutor_id == tutor_id)
            .options(selectinload(TutorProfile.subjects), selectinload(TutorProfile.evidences))
            .order_by(TutorProfile.is_default.desc(), TutorProfile.updated_at.desc())
        )
        return list(self.db.scalars(statement))

    def get_for_tutor(
        self, tutor_id: UUID, profile_id: UUID, *, for_update: bool = False
    ) -> TutorProfile | None:
        statement = (
            select(TutorProfile)
            .where(TutorProfile.id == profile_id, TutorProfile.tutor_id == tutor_id)
            .options(selectinload(TutorProfile.subjects), selectinload(TutorProfile.evidences))
        )
        if for_update:
            statement = statement.with_for_update().execution_options(populate_existing=True)
        return self.db.scalar(statement)

    def clear_default(self, tutor_id: UUID) -> None:
        self.db.execute(
            update(TutorProfile)
            .where(TutorProfile.tutor_id == tutor_id, TutorProfile.is_default.is_(True))
            .values(is_default=False)
        )

    def add(self, entity: TutorProfile | TutorProfileEvidence) -> None:
        self.db.add(entity)

    def delete(self, entity: TutorProfileEvidence) -> None:
        self.db.delete(entity)

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
