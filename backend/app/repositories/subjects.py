from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Subject


class SubjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> list[Subject]:
        return list(self.db.scalars(select(Subject).order_by(Subject.id)))

    def find_by_ids(self, subject_ids: Iterable[int]) -> list[Subject]:
        ids = list(subject_ids)
        if not ids:
            return []
        return list(self.db.scalars(select(Subject).where(Subject.id.in_(ids))))
