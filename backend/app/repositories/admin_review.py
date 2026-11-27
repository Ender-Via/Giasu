from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.constants import TutorProfileStatus
from app.core.recruitment_status import TutorApplicationStatus, TutorRequestStatus
from app.db.models import Parent, Tutor, TutorApplication, TutorProfile, TutorRequest


class AdminReviewRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_tutor_profiles(
        self, *, status: str, page: int, page_size: int
    ) -> tuple[list[TutorProfile], int]:
        filters = [TutorProfile.status == status]
        total = int(
            self.db.scalar(select(func.count()).select_from(TutorProfile).where(*filters)) or 0
        )
        if status == TutorProfileStatus.PENDING_REVIEW:
            ordering = (
                TutorProfile.submitted_at.asc(),
                TutorProfile.created_at.asc(),
                TutorProfile.id.asc(),
            )
        else:
            ordering = (TutorProfile.reviewed_at.desc(), TutorProfile.id.desc())

        statement = (
            select(TutorProfile)
            .where(*filters)
            .options(
                selectinload(TutorProfile.subjects),
                selectinload(TutorProfile.evidences),
                joinedload(TutorProfile.tutor).joinedload(Tutor.user),
                joinedload(TutorProfile.reviewer),
            )
            .order_by(*ordering)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(statement)), total

    def get_tutor_profile(
        self, profile_id: UUID, *, populate_existing: bool = False
    ) -> TutorProfile | None:
        statement = (
            select(TutorProfile)
            .where(TutorProfile.id == profile_id)
            .options(
                selectinload(TutorProfile.subjects),
                selectinload(TutorProfile.evidences),
                joinedload(TutorProfile.tutor).joinedload(Tutor.user),
                joinedload(TutorProfile.reviewer),
            )
        )
        if populate_existing:
            statement = statement.execution_options(populate_existing=True)
        return self.db.scalar(statement)

    def transition_tutor_profile(
        self,
        profile_id: UUID,
        *,
        to_status: str,
        reviewed_by: UUID,
        reviewed_at: datetime,
        reject_reason: str | None = None,
    ) -> bool:
        result = self.db.execute(
            update(TutorProfile)
            .where(
                TutorProfile.id == profile_id,
                TutorProfile.status == TutorProfileStatus.PENDING_REVIEW,
            )
            .values(
                status=to_status,
                reject_reason=reject_reason,
                reviewed_by=reviewed_by,
                reviewed_at=reviewed_at,
                updated_at=reviewed_at,
            )
        )
        return result.rowcount > 0

    def list_tutor_requests(
        self, *, status: str, page: int, page_size: int
    ) -> tuple[list[tuple[TutorRequest, int]], int]:
        filters = [TutorRequest.status == status]
        total = int(
            self.db.scalar(select(func.count()).select_from(TutorRequest).where(*filters)) or 0
        )
        open_count = (
            select(func.count())
            .select_from(TutorApplication)
            .where(
                TutorApplication.request_id == TutorRequest.id,
                TutorApplication.status.in_(TutorApplicationStatus.OPEN),
            )
            .correlate(TutorRequest)
            .scalar_subquery()
        )
        if status == TutorRequestStatus.PENDING_REVIEW:
            ordering = (TutorRequest.submitted_at.asc(), TutorRequest.id.asc())
        else:
            ordering = (
                TutorRequest.reviewed_at.desc(),
                TutorRequest.updated_at.desc(),
                TutorRequest.id.desc(),
            )

        statement = (
            select(TutorRequest, open_count)
            .where(*filters)
            .options(
                selectinload(TutorRequest.student),
                selectinload(TutorRequest.subject),
                joinedload(TutorRequest.parent).joinedload(Parent.user),
                joinedload(TutorRequest.reviewer),
            )
            .order_by(*ordering)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return [(request, int(count or 0)) for request, count in self.db.execute(statement)], total

    def get_tutor_request(
        self, request_id: UUID, *, populate_existing: bool = False
    ) -> TutorRequest | None:
        statement = (
            select(TutorRequest)
            .where(TutorRequest.id == request_id)
            .options(
                selectinload(TutorRequest.student),
                selectinload(TutorRequest.subject),
                joinedload(TutorRequest.parent).joinedload(Parent.user),
                joinedload(TutorRequest.reviewer),
            )
        )
        if populate_existing:
            statement = statement.execution_options(populate_existing=True)
        return self.db.scalar(statement)

    def count_open_applications(self, request_id: UUID) -> int:
        statement = (
            select(func.count())
            .select_from(TutorApplication)
            .where(
                TutorApplication.request_id == request_id,
                TutorApplication.status.in_(TutorApplicationStatus.OPEN),
            )
        )
        return int(self.db.scalar(statement) or 0)

    def transition_tutor_request(
        self,
        request_id: UUID,
        *,
        to_status: str,
        reviewed_by: UUID,
        reviewed_at: datetime,
        expires_at: datetime | None,
        reject_reason: str | None = None,
    ) -> bool:
        result = self.db.execute(
            update(TutorRequest)
            .where(
                TutorRequest.id == request_id,
                TutorRequest.status == TutorRequestStatus.PENDING_REVIEW,
            )
            .values(
                status=to_status,
                reject_reason=reject_reason,
                reviewed_by=reviewed_by,
                reviewed_at=reviewed_at,
                expires_at=expires_at,
                updated_at=reviewed_at,
            )
        )
        return result.rowcount > 0

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
