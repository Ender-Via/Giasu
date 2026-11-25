import io
import json
from datetime import datetime, timezone
from urllib.error import HTTPError
from uuid import uuid4

import pytest
from httpx import AsyncClient
from pydantic import SecretStr
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.supabase_auth import (
    SupabaseAuthClient,
    SupabaseDuplicateEmailError,
    SupabaseRateLimitError,
    SupabaseSignUpResult,
    SupabaseUnavailableError,
    get_supabase_auth_client,
)
from app.db.models import Parent, Tutor, User
from app.main import app

pytestmark = pytest.mark.anyio


class FakeSupabaseAuthClient:
    def __init__(self, db: Session, error: Exception | None = None) -> None:
        self.db = db
        self.error = error
        self.calls: list[dict[str, object]] = []

    def sign_up(self, **kwargs: object) -> SupabaseSignUpResult:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error

        auth_user_id = uuid4()
        business_user_id = uuid4()
        role = str(kwargs["role"])
        user = User(
            id=business_user_id,
            auth_user_id=auth_user_id,
            role_id=2 if role == "Tutor" else 3,
            full_name=str(kwargs["full_name"]),
            login_identifier=str(kwargs["email"]),
            credential_reference=None,
            is_active=True,
            token_version=0,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(user)
        if role == "Tutor":
            self.db.add(
                Tutor(
                    user_id=business_user_id,
                    phone=str(kwargs["phone"]),
                    verification_status="Unverified",
                    reputation_score=None,
                )
            )
        else:
            self.db.add(
                Parent(
                    user_id=business_user_id,
                    phone=str(kwargs["phone"]),
                    reputation_score=None,
                )
            )
        self.db.commit()
        return SupabaseSignUpResult(auth_user_id=auth_user_id)


def registration_payload(role: str = "Tutor") -> dict[str, object]:
    return {
        "role": role,
        "fullName": "  Nguyễn   Văn Lộc  ",
        "phone": "0912345678",
        "email": "LOC.S01-04@Example.com",
        "password": "MatKhau123",
        "acceptTerms": True,
    }


@pytest.mark.parametrize("role", ["Tutor", "Parent"])
async def test_register_creates_business_user_and_exactly_one_role_profile(
    client: AsyncClient, db_session: Session, role: str
) -> None:
    # AC-AUTH-01, BR-01
    fake = FakeSupabaseAuthClient(db_session)
    app.dependency_overrides[get_supabase_auth_client] = lambda: fake

    response = await client.post("/api/auth/register", json=registration_payload(role))

    assert response.status_code == 201
    assert response.json()["data"]["fullName"] == "Nguyễn Văn Lộc"
    assert response.json()["data"]["role"] == role
    user = db_session.scalar(select(User).where(User.login_identifier == "loc.s01-04@example.com"))
    assert user is not None
    assert user.credential_reference is None
    assert user.is_active is True
    if role == "Tutor":
        tutor = db_session.get(Tutor, user.id)
        assert tutor is not None
        assert tutor.reputation_score is None
        assert db_session.get(Parent, user.id) is None
    else:
        parent = db_session.get(Parent, user.id)
        assert parent is not None
        assert parent.reputation_score is None
        assert db_session.get(Tutor, user.id) is None
    tutor_count = db_session.scalar(select(func.count()).select_from(Tutor))
    parent_count = db_session.scalar(select(func.count()).select_from(Parent))
    assert tutor_count == (1 if role == "Tutor" else 0)
    assert parent_count == (1 if role == "Parent" else 0)
    assert fake.calls[0]["email"] == "loc.s01-04@example.com"
    assert fake.calls[0]["password"] == "MatKhau123"


@pytest.mark.parametrize(
    ("change", "expected_error"),
    [
        ({"password": "12345678"}, "Mật khẩu từ 8 đến 128 ký tự, có cả chữ và số."),
        ({"phone": "123"}, "Số điện thoại gồm 10 chữ số, bắt đầu bằng 0."),
        ({"acceptTerms": False}, "Bạn cần đồng ý quy chế để tiếp tục."),
        ({"role": "Admin"}, "Vui lòng chọn vai trò Gia sư hoặc Phụ huynh."),
        ({"role": None}, "Vui lòng chọn vai trò Gia sư hoặc Phụ huynh."),
        ({"fullName": "A"}, "Họ tên từ 2 đến 100 ký tự."),
        ({"fullName": None}, "Họ tên từ 2 đến 100 ký tự."),
        ({"email": "not-an-email"}, "Email không đúng định dạng."),
        ({"email": None}, "Email không đúng định dạng."),
    ],
)
async def test_register_rejects_each_invalid_field_without_creating_account(
    client: AsyncClient,
    db_session: Session,
    change: dict[str, object],
    expected_error: str,
) -> None:
    # AC-AUTH-02, BR-01
    fake = FakeSupabaseAuthClient(db_session)
    app.dependency_overrides[get_supabase_auth_client] = lambda: fake
    payload = registration_payload()
    payload.update(change)

    response = await client.post("/api/auth/register", json=payload)

    assert response.status_code == 400
    assert response.json()["errors"] == [expected_error]
    assert fake.calls == []
    assert db_session.scalar(select(func.count()).select_from(User)) == 0


async def test_register_rejects_duplicate_email_case_insensitively_before_supabase(
    client: AsyncClient, db_session: Session
) -> None:
    # AC-AUTH-03, BR-01
    existing_auth_id = uuid4()
    existing = User(
        id=uuid4(),
        auth_user_id=existing_auth_id,
        role_id=2,
        full_name="Gia Sư Có Sẵn",
        login_identifier="Loc.S01-04@Example.com",
        credential_reference=None,
        is_active=True,
        token_version=0,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(existing)
    db_session.commit()
    fake = FakeSupabaseAuthClient(db_session)
    app.dependency_overrides[get_supabase_auth_client] = lambda: fake

    response = await client.post("/api/auth/register", json=registration_payload())

    assert response.status_code == 409
    assert response.json()["message"] == "Email đã được sử dụng."
    assert fake.calls == []
    assert db_session.scalar(select(func.count()).select_from(User)) == 1


async def test_register_maps_supabase_hidden_duplicate_to_409(
    client: AsyncClient, db_session: Session
) -> None:
    # AC-AUTH-03 khi Supabase phát hiện xung đột trước DB nghiệp vụ.
    fake = FakeSupabaseAuthClient(db_session, SupabaseDuplicateEmailError())
    app.dependency_overrides[get_supabase_auth_client] = lambda: fake

    response = await client.post("/api/auth/register", json=registration_payload())

    assert response.status_code == 409
    assert response.json()["message"] == "Email đã được sử dụng."
    assert db_session.scalar(select(func.count()).select_from(User)) == 0


async def test_register_maps_supabase_rate_limit_to_429_without_profile(
    client: AsyncClient, db_session: Session
) -> None:
    # AC-AUTH-05, D08
    fake = FakeSupabaseAuthClient(db_session, SupabaseRateLimitError())
    app.dependency_overrides[get_supabase_auth_client] = lambda: fake

    response = await client.post("/api/auth/register", json=registration_payload())

    assert response.status_code == 429
    assert "60 giây" in response.json()["message"]
    assert db_session.scalar(select(func.count()).select_from(User)) == 0


async def test_register_maps_supabase_unavailable_to_503(
    client: AsyncClient, db_session: Session
) -> None:
    fake = FakeSupabaseAuthClient(db_session, SupabaseUnavailableError("Service down"))
    app.dependency_overrides[get_supabase_auth_client] = lambda: fake

    response = await client.post("/api/auth/register", json=registration_payload())

    assert response.status_code == 503
    assert "Chưa thể tạo tài khoản" in response.json()["message"]
    assert db_session.scalar(select(func.count()).select_from(User)) == 0


async def test_register_ignores_x_forwarded_for_from_untrusted_client(
    client: AsyncClient, db_session: Session
) -> None:
    fake = FakeSupabaseAuthClient(db_session)
    app.dependency_overrides[get_supabase_auth_client] = lambda: fake

    response = await client.post(
        "/api/auth/register",
        json=registration_payload(),
        headers={"X-Forwarded-For": "203.0.113.195, 10.0.0.1"},
    )

    assert response.status_code == 201
    assert fake.calls[0]["client_ip"] == "127.0.0.1"


async def test_register_forwards_x_forwarded_for_from_trusted_proxy(
    client: AsyncClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeSupabaseAuthClient(db_session)
    app.dependency_overrides[get_supabase_auth_client] = lambda: fake
    monkeypatch.setattr(
        "app.api.auth.get_settings",
        lambda: Settings(trusted_proxies=["127.0.0.1"]),
    )

    response = await client.post(
        "/api/auth/register",
        json=registration_payload(),
        headers={"X-Forwarded-For": "203.0.113.195, 10.0.0.1"},
    )

    assert response.status_code == 201
    assert fake.calls[0]["client_ip"] == "203.0.113.195"


def test_supabase_auth_client_unwraps_secret_str_and_sends_string_apikey(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    auth_user_id = uuid4()
    captured: dict[str, object] = {}

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(
                {"user": {"id": str(auth_user_id), "identities": [{"id": "1"}]}}
            ).encode("utf-8")

    def fake_urlopen(request: object, timeout: int = 10) -> FakeResponse:
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("app.core.supabase_auth.urlopen", fake_urlopen)
    client_auth = SupabaseAuthClient(
        Settings(
            supabase_url="https://example.supabase.co",
            supabase_secret_key=SecretStr("sb_secret_test_value"),
        )
    )

    result = client_auth.sign_up(
        email="tutor@example.com",
        password="MatKhau123",
        full_name="Nguyễn Văn Lộc",
        phone="0912345678",
        role="Tutor",
        client_ip="1.2.3.4",
    )

    assert result.auth_user_id == auth_user_id
    req = captured["request"]
    assert req.get_header("Apikey") == "sb_secret_test_value"  # type: ignore[attr-defined]
    assert isinstance(req.get_header("Apikey"), str)  # type: ignore[attr-defined]
    assert req.get_header("Sb-forwarded-for") == "1.2.3.4"  # type: ignore[attr-defined]


def test_supabase_auth_client_missing_secret_raises_unavailable() -> None:
    client_auth = SupabaseAuthClient(Settings(supabase_secret_key=None))
    with pytest.raises(SupabaseUnavailableError):
        client_auth.sign_up(
            email="tutor@example.com",
            password="MatKhau123",
            full_name="Nguyễn Văn Lộc",
            phone="0912345678",
            role="Tutor",
            client_ip=None,
        )


def test_supabase_auth_client_empty_identities_raises_duplicate_email(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps({"user": {"id": str(uuid4()), "identities": []}}).encode("utf-8")

    monkeypatch.setattr("app.core.supabase_auth.urlopen", lambda req, timeout=10: FakeResponse())
    client_auth = SupabaseAuthClient(Settings(supabase_secret_key=SecretStr("sb_secret_test")))

    with pytest.raises(SupabaseDuplicateEmailError):
        client_auth.sign_up(
            email="tutor@example.com",
            password="MatKhau123",
            full_name="Nguyễn Văn Lộc",
            phone="0912345678",
            role="Tutor",
            client_ip=None,
        )


@pytest.mark.parametrize(
    ("status_code", "body", "expected_exc"),
    [
        (422, {"code": 422, "error_code": "email_exists"}, SupabaseDuplicateEmailError),
        (429, {"code": 429, "msg": "Too many requests"}, SupabaseRateLimitError),
    ],
)
def test_supabase_auth_client_maps_gotrue_v2_http_errors(
    monkeypatch: pytest.MonkeyPatch,
    status_code: int,
    body: dict[str, object],
    expected_exc: type[Exception],
) -> None:
    def fake_urlopen(request: object, timeout: int = 10) -> object:
        raise HTTPError(
            url="https://example.supabase.co/auth/v1/signup",
            code=status_code,
            msg="Error",
            hdrs=None,  # type: ignore[arg-type]
            fp=io.BytesIO(json.dumps(body).encode("utf-8")),
        )

    monkeypatch.setattr("app.core.supabase_auth.urlopen", fake_urlopen)
    client_auth = SupabaseAuthClient(Settings(supabase_secret_key=SecretStr("sb_secret_test")))

    with pytest.raises(expected_exc):
        client_auth.sign_up(
            email="tutor@example.com",
            password="MatKhau123",
            full_name="Nguyễn Văn Lộc",
            phone="0912345678",
            role="Tutor",
            client_ip=None,
        )

