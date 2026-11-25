import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import UUID

from app.core.config import Settings, get_settings


class SupabaseSignUpError(Exception):
    pass


class SupabaseDuplicateEmailError(SupabaseSignUpError):
    pass


class SupabaseRateLimitError(SupabaseSignUpError):
    pass


class SupabaseUnavailableError(SupabaseSignUpError):
    pass


@dataclass(frozen=True)
class SupabaseSignUpResult:
    auth_user_id: UUID


class SupabaseAuthClient:
    """Client tối thiểu cho Auth signup; không lưu hoặc ghi log mật khẩu."""

    def __init__(self, settings: Settings) -> None:
        self._url = f"{settings.supabase_url.rstrip('/')}/auth/v1/signup"
        secret = settings.supabase_secret_key
        self._secret_key = secret.get_secret_value() if secret is not None else ""

    def sign_up(
        self,
        *,
        email: str,
        password: str,
        full_name: str,
        phone: str,
        role: str,
        client_ip: str | None,
    ) -> SupabaseSignUpResult:
        if not self._secret_key:
            raise SupabaseUnavailableError("Thiếu SUPABASE_SECRET_KEY ở backend.")

        body = json.dumps(
            {
                "email": email,
                "password": password,
                "data": {
                    "registration_source": "giasu-register",
                    "full_name": full_name,
                    "phone": phone,
                    "role": role,
                    "accept_terms": True,
                },
            }
        ).encode("utf-8")
        headers = {
            "apikey": self._secret_key,
            "Content-Type": "application/json",
        }
        if client_ip:
            headers["Sb-Forwarded-For"] = client_ip

        request = Request(self._url, data=body, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=10) as response:  # noqa: S310
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            self._raise_http_error(exc)
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise SupabaseUnavailableError("Không thể kết nối Supabase Auth.") from exc

        user = payload.get("user") or payload
        identities = user.get("identities")
        if isinstance(identities, list) and len(identities) == 0:
            raise SupabaseDuplicateEmailError("Email đã được sử dụng.")
        try:
            return SupabaseSignUpResult(auth_user_id=UUID(user["id"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise SupabaseUnavailableError("Supabase Auth trả dữ liệu không hợp lệ.") from exc

    @staticmethod
    def _raise_http_error(exc: HTTPError) -> None:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            payload = {}

        code = str(payload.get("error_code") or payload.get("code") or "").lower()
        message = str(
            payload.get("msg") or payload.get("message") or payload.get("error_description") or ""
        ).lower()
        if exc.code == 429:
            raise SupabaseRateLimitError from exc
        if code in {"email_exists", "user_already_exists", "user_already_registered"} or any(
            marker in message
            for marker in ("already registered", "already exists", "email exists")
        ):
            raise SupabaseDuplicateEmailError from exc
        raise SupabaseUnavailableError("Supabase Auth từ chối yêu cầu đăng ký.") from exc


def get_supabase_auth_client() -> SupabaseAuthClient:
    return SupabaseAuthClient(get_settings())
