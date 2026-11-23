from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    ARRAY,
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    Text,
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


class Parent(Base):
    __tablename__ = "parents"

    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", name="fk_parents_users_user_id", ondelete="RESTRICT"),
        primary_key=True,
    )
    phone: Mapped[str] = mapped_column(Text, nullable=False)
    reputation_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)


class Subject(Base):
    __tablename__ = "subjects"
    __table_args__ = (Index("ix_subjects_name", "name", unique=True),)

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)


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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    subjects: Mapped[list[Subject]] = relationship(
        secondary="tutor_profile_subjects", order_by=Subject.id
    )
    evidences: Mapped[list["TutorProfileEvidence"]] = relationship(
        back_populates="profile",
        order_by="(TutorProfileEvidence.created_at, TutorProfileEvidence.id)",
    )


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
