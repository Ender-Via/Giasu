from uuid import UUID

from app.core.supabase_auth import (
    SupabaseAuthClient,
    SupabaseDuplicateEmailError,
    SupabaseRateLimitError,
    SupabaseUnavailableError,
)
from app.repositories.auth import AuthRepository
from app.schemas.auth import CurrentUserResponse, RegisterRequest, RoleName

ROLE_NAMES: dict[int, RoleName] = {1: "Admin", 2: "Tutor", 3: "Parent"}


class AccountLockedError(Exception):
    pass


class DuplicateEmailError(Exception):
    pass


class RegistrationRateLimitError(Exception):
    pass


class RegistrationUnavailableError(Exception):
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

    def register(
        self,
        request: RegisterRequest,
        supabase: SupabaseAuthClient,
        client_ip: str | None,
    ) -> CurrentUserResponse:
        if self.repository.find_by_email(request.email) is not None:
            raise DuplicateEmailError

        try:
            result = supabase.sign_up(
                email=request.email,
                password=request.password.get_secret_value(),
                full_name=request.fullName,
                phone=request.phone,
                role=request.role,
                client_ip=client_ip,
            )
        except SupabaseDuplicateEmailError as exc:
            raise DuplicateEmailError from exc
        except SupabaseRateLimitError as exc:
            raise RegistrationRateLimitError from exc
        except SupabaseUnavailableError as exc:
            raise RegistrationUnavailableError from exc

        user = self.repository.find_by_auth_user_id(result.auth_user_id)
        if user is None:
            if self.repository.find_by_email(request.email) is not None:
                raise DuplicateEmailError
            raise RegistrationUnavailableError

        role = ROLE_NAMES.get(user.role_id)
        if role not in ("Tutor", "Parent"):
            raise RegistrationUnavailableError
        return CurrentUserResponse(userId=user.id, fullName=user.full_name, role=role)
