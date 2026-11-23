from uuid import UUID

from app.repositories.auth import AuthRepository
from app.schemas.auth import CurrentUserResponse, RoleName

ROLE_NAMES: dict[int, RoleName] = {1: "Admin", 2: "Tutor", 3: "Parent"}


class AccountLockedError(Exception):
    pass


class AuthService:
    def __init__(self, repository: AuthRepository) -> None:
        self.repository = repository

    def get_current_user(self, auth_user_id: UUID) -> CurrentUserResponse | None:
        user = self.repository.find_by_auth_user_id(auth_user_id)
        if user is None:
            return None
        if not user.is_active:
            raise AccountLockedError

        role = ROLE_NAMES.get(user.role_id)
        if role is None:
            return None

        return CurrentUserResponse(userId=user.id, fullName=user.full_name, role=role)
