from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


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
