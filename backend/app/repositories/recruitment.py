from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.recruitment_status import TutorApplicationStatus, TutorRequestStatus
from app.db.models import Parent, Student, TutorApplication, TutorRequest, User


class RecruitmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_parent(self, parent_id: UUID) -> Parent | None:
        return self.db.get(Parent, parent_id)

    def get_parent_contact(self, parent_id: UUID) -> tuple[User, Parent]:
        statement = select(User, Parent).join(Parent).where(User.id == parent_id)
        user, parent = self.db.execute(statement).one()
        return user, parent

    def list_students(self, parent_id: UUID) -> list[Student]:
        statement = (
            select(Student)
            .where(Student.parent_id == parent_id)
            .order_by(Student.created_at, Student.id)
        )
        return list(self.db.scalars(statement))

    def get_student(self, parent_id: UUID, student_id: UUID) -> Student | None:
        statement = select(Student).where(Student.id == student_id, Student.parent_id == parent_id)
        return self.db.scalar(statement)

    def list_requests(
        self,
        parent_id: UUID,
        status: str | None,
        student_id: UUID | None,
        page: int,
        page_size: int,
    ) -> tuple[list[tuple[TutorRequest, int]], int]:
        filters = [TutorRequest.parent_id == parent_id]
        if status is not None:
            filters.append(TutorRequest.status == status)
        if student_id is not None:
            filters.append(TutorRequest.student_id == student_id)
        total = self.db.scalar(select(func.count()).select_from(TutorRequest).where(*filters)) or 0
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
        statement = (
            select(TutorRequest, open_count)
            .where(*filters)
            .options(selectinload(TutorRequest.student), selectinload(TutorRequest.subject))
            .order_by(TutorRequest.updated_at.desc(), TutorRequest.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return [(request, count) for request, count in self.db.execute(statement)], total

    def get_request(
        self,
        request_id: UUID,
        *,
        parent_id: UUID | None = None,
        recruiting_only: bool = False,
        for_update: bool = False,
    ) -> TutorRequest | None:
        statement = (
            select(TutorRequest)
            .where(TutorRequest.id == request_id)
            .options(
                selectinload(TutorRequest.student),
                selectinload(TutorRequest.subject),
                selectinload(TutorRequest.reviewer),
            )
        )
        if parent_id is not None:
            statement = statement.where(TutorRequest.parent_id == parent_id)
        if recruiting_only:
            statement = statement.where(TutorRequest.status == TutorRequestStatus.RECRUITING)
        if for_update:
            statement = statement.with_for_update().execution_options(populate_existing=True)
        return self.db.scalar(statement)

    def count_open_applications(self, request_id: UUID, tutor_id: UUID | None = None) -> int:
        statement = (
            select(func.count())
            .select_from(TutorApplication)
            .where(
                TutorApplication.request_id == request_id,
                TutorApplication.status.in_(TutorApplicationStatus.OPEN),
            )
        )
        if tutor_id is not None:
            statement = statement.where(TutorApplication.tutor_id == tutor_id)
        return self.db.scalar(statement) or 0

    def lock_open_applications(self, request_id: UUID) -> list[TutorApplication]:
        # Mọi luồng ghi vào phiếu phải khóa tin trước khi kiểm trạng thái và ghi phiếu.
        statement = (
            select(TutorApplication)
            .where(
                TutorApplication.request_id == request_id,
                TutorApplication.status.in_(TutorApplicationStatus.OPEN),
            )
            .order_by(TutorApplication.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        return list(self.db.scalars(statement))

    def add(self, entity: Student | TutorRequest) -> None:
        self.db.add(entity)

    def commit(self) -> None:
        self.db.commit()
