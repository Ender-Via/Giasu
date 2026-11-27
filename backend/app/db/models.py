from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    ARRAY,
    JSON,
    Boolean,
    Computed,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

TextArray = ARRAY(Text).with_variant(JSON(), "sqlite")


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = (Index("ix_roles_name", "name", unique=True),)

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    users: Mapped[list["User"]] = relationship(back_populates="role")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_auth_user_id", "auth_user_id", unique=True),
        Index("ix_users_login_identifier", "login_identifier", unique=True),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    # FK auth.users.id được Alembic 0002 tạo; không khai báo ORM vì app không sở hữu schema auth.
    auth_user_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    role_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("roles.id", name="fk_users_roles_role_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    login_identifier: Mapped[str] = mapped_column(Text, nullable=False)
    credential_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    token_version: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    role: Mapped[Role] = relationship(back_populates="users")
    tutor: Mapped["Tutor | None"] = relationship(back_populates="user", uselist=False)
    parent: Mapped["Parent | None"] = relationship(back_populates="user", uselist=False)


class Tutor(Base):
    __tablename__ = "tutors"

    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", name="fk_tutors_users_user_id", ondelete="RESTRICT"),
        primary_key=True,
    )
    phone: Mapped[str] = mapped_column(Text, nullable=False)
    verification_status: Mapped[str] = mapped_column(
        Text, nullable=False, default="Unverified", server_default="Unverified"
    )
    reputation_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    user: Mapped[User] = relationship(back_populates="tutor")


class Parent(Base):
    __tablename__ = "parents"

    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", name="fk_parents_users_user_id", ondelete="RESTRICT"),
        primary_key=True,
    )
    phone: Mapped[str] = mapped_column(Text, nullable=False)
    reputation_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    user: Mapped[User] = relationship(back_populates="parent")


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint("parent_id", "id", name="uq_students_parent_id_id"),
        Index("ix_students_parent_created", "parent_id", "created_at", "id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    parent_id: Mapped[UUID] = mapped_column(
        ForeignKey("parents.user_id", name="fk_students_parent_id", ondelete="RESTRICT")
    )
    full_name: Mapped[str] = mapped_column(Text)
    grade_level: Mapped[int] = mapped_column(SmallInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Subject(Base):
    __tablename__ = "subjects"
    __table_args__ = (
        Index("ix_subjects_name", "name", unique=True),
        Index("ix_subjects_code", "code", unique=True),
    )

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    code: Mapped[str] = mapped_column(
        Text, Computed("'SUB-' || CAST(id AS VARCHAR(6))", persisted=True)
    )


class TutorRequest(Base):
    __tablename__ = "tutor_requests"
    __table_args__ = (
        ForeignKeyConstraint(
            ["parent_id", "student_id"],
            ["students.parent_id", "students.id"],
            name="fk_tutor_requests_parent_student",
            ondelete="RESTRICT",
        ),
        Index("ix_tutor_requests_parent_updated", "parent_id", "updated_at", "id"),
        Index("ix_tutor_requests_student_id", "student_id"),
        Index("ix_tutor_requests_subject_id", "subject_id"),
        Index("ix_tutor_requests_status_submitted", "status", "submitted_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    parent_id: Mapped[UUID] = mapped_column(
        ForeignKey("parents.user_id", name="fk_tutor_requests_parent_id", ondelete="RESTRICT")
    )
    student_id: Mapped[UUID] = mapped_column(Uuid)
    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", name="fk_tutor_requests_subject_id", ondelete="RESTRICT")
    )
    title: Mapped[str | None] = mapped_column(Text)
    education_level: Mapped[str] = mapped_column(Text)
    teaching_mode: Mapped[str] = mapped_column(Text)
    province: Mapped[str | None] = mapped_column(Text)
    ward: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    sessions_per_week: Mapped[int] = mapped_column(SmallInteger)
    min_fee: Mapped[int] = mapped_column(Integer)
    max_fee: Mapped[int] = mapped_column(Integer)
    requirements: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default="PendingReview")
    reject_reason: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reviewed_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", name="fk_tutor_requests_reviewed_by", ondelete="RESTRICT")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    student: Mapped[Student] = relationship()
    subject: Mapped[Subject] = relationship()
    parent: Mapped[Parent] = relationship(foreign_keys=[parent_id], overlaps="student")
    reviewer: Mapped[User | None] = relationship(foreign_keys=[reviewed_by])


class TutorApplication(Base):
    __tablename__ = "tutor_applications"
    __table_args__ = (
        Index("ix_tutor_applications_request_status", "request_id", "status"),
        Index("ix_tutor_applications_tutor_status", "tutor_id", "status"),
        Index(
            "ux_tutor_applications_open",
            "request_id",
            "tutor_id",
            unique=True,
            postgresql_where=text("status IN ('Pending', 'Viewed', 'TrialInvited')"),
            sqlite_where=text("status IN ('Pending', 'Viewed', 'TrialInvited')"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "tutor_requests.id", name="fk_tutor_applications_request_id", ondelete="RESTRICT"
        )
    )
    tutor_id: Mapped[UUID] = mapped_column(
        ForeignKey("tutors.user_id", name="fk_tutor_applications_tutor_id", ondelete="RESTRICT")
    )
    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "tutor_profiles.id", name="fk_tutor_applications_profile_id", ondelete="RESTRICT"
        )
    )
    introduction: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default="Pending")
    trial_scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    trial_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_logs_entity_entity_id", "entity", "entity_id"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    actor_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", name="fk_audit_logs_actor_id", ondelete="RESTRICT")
    )
    entity: Mapped[str] = mapped_column(Text)
    entity_id: Mapped[UUID] = mapped_column(Uuid)
    action: Mapped[str] = mapped_column(Text)
    from_status: Mapped[str | None] = mapped_column(Text)
    to_status: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class TutorProfileSubject(Base):
    __tablename__ = "tutor_profile_subjects"
    __table_args__ = (Index("ix_tutor_profile_subjects_subject_id", "subject_id"),)

    profile_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey(
            "tutor_profiles.id", name="fk_tutor_profile_subjects_profile_id", ondelete="RESTRICT"
        ),
        primary_key=True,
    )
    subject_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("subjects.id", name="fk_tutor_profile_subjects_subject_id", ondelete="RESTRICT"),
        primary_key=True,
    )


class TutorProfile(Base):
    __tablename__ = "tutor_profiles"
    __table_args__ = (
        Index("ix_tutor_profiles_tutor_id", "tutor_id"),
        Index("ix_tutor_profiles_reviewed_by", "reviewed_by"),
        Index(
            "ux_tutor_profiles_tutor_id_default",
            "tutor_id",
            unique=True,
            postgresql_where=text("is_default"),
            sqlite_where=text("is_default"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tutor_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("tutors.user_id", name="fk_tutor_profiles_tutor_id", ondelete="RESTRICT"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    education_level: Mapped[str] = mapped_column(Text, nullable=False)
    teaching_mode: Mapped[str] = mapped_column(Text, nullable=False)
    province: Mapped[str] = mapped_column(Text, nullable=False)
    teaching_wards: Mapped[list[str]] = mapped_column(TextArray, nullable=False, default=list)
    expected_fee_per_session: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="Draft")
    availability: Mapped[str] = mapped_column(Text, nullable=False, default="Accepting")
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reject_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", name="fk_tutor_profiles_reviewed_by", ondelete="RESTRICT"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    subjects: Mapped[list[Subject]] = relationship(
        secondary="tutor_profile_subjects", order_by=Subject.id
    )
    evidences: Mapped[list["TutorProfileEvidence"]] = relationship(
        back_populates="profile",
        order_by="(TutorProfileEvidence.created_at, TutorProfileEvidence.id)",
    )
    tutor: Mapped[Tutor] = relationship(foreign_keys=[tutor_id])
    reviewer: Mapped[User | None] = relationship(foreign_keys=[reviewed_by])


class TutorProfileEvidence(Base):
    __tablename__ = "tutor_profile_evidences"
    __table_args__ = (
        Index("ix_tutor_profile_evidences_profile_id", "profile_id"),
        Index("ux_tutor_profile_evidences_file_ref", "file_ref", unique=True),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    profile_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey(
            "tutor_profiles.id", name="fk_tutor_profile_evidences_profile_id", ondelete="RESTRICT"
        ),
        nullable=False,
    )
    file_ref: Mapped[str] = mapped_column(Text, nullable=False)
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    profile: Mapped[TutorProfile] = relationship(back_populates="evidences")


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index(
            "ix_notifications_recipient_is_read_created_at",
            "recipient_id",
            "is_read",
            "created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    recipient_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", name="fk_notifications_recipient_id", ondelete="RESTRICT"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    link: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_read: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", name="fk_notification_preferences_user_id", ondelete="RESTRICT"),
        primary_key=True,
    )
    type: Mapped[str] = mapped_column(Text, primary_key=True)
    email_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )


class StudentVerification(Base):
    __tablename__ = "student_verifications"
    __table_args__ = (
        Index("ix_student_verifications_tutor_id", "tutor_id"),
        Index("ix_student_verifications_status_created_at", "status", "created_at"),
        Index("ix_student_verifications_reviewed_by", "reviewed_by"),
        Index(
            "ux_student_verifications_evidence_file_ref",
            "evidence_file_ref",
            unique=True,
        ),
        Index(
            "ux_student_verifications_tutor_id_pending",
            "tutor_id",
            unique=True,
            postgresql_where=text("status = 'Pending'"),
            sqlite_where=text("status = 'Pending'"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tutor_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey(
            "tutors.user_id", name="fk_student_verifications_tutor_id", ondelete="RESTRICT"
        ),
        nullable=False,
    )
    university: Mapped[str] = mapped_column(Text, nullable=False)
    student_code: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_file_ref: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="Pending", server_default="Pending"
    )
    reject_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            "users.id", name="fk_student_verifications_reviewed_by", ondelete="RESTRICT"
        ),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    tutor: Mapped[Tutor] = relationship(foreign_keys=[tutor_id])
    reviewer: Mapped[User | None] = relationship(foreign_keys=[reviewed_by])
