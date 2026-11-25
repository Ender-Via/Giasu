from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import User


class AuthRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def find_by_auth_user_id(self, auth_user_id: UUID) -> User | None:
        statement = select(User).where(User.auth_user_id == auth_user_id)
        return self.db.scalar(statement)

    def find_by_email(self, email: str) -> User | None:
        statement = select(User).where(func.lower(User.login_identifier) == email.lower())
        return self.db.scalar(statement)
