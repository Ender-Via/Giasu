from datetime import timedelta
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_me_returns_business_profile_for_valid_supabase_token(
    client: AsyncClient, add_user, make_token
) -> None:
    auth_user_id = uuid4()
    user = add_user(auth_user_id=auth_user_id, role_id=2)

    response = await client.get("/api/auth/me", headers=bearer(make_token(auth_user_id)))

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.json() == {
        "success": True,
        "data": {
            "userId": str(user.id),
            "fullName": "Nguyễn Văn Gia Sư",
            "role": "Tutor",
        },
        "message": None,
        "errors": None,
    }


async def test_me_rejects_missing_token(client: AsyncClient) -> None:
    response = await client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["message"] == "Bạn cần đăng nhập để tiếp tục."


async def test_me_rejects_token_with_wrong_signature(client: AsyncClient, make_token) -> None:
    attacker_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = make_token(uuid4(), signing_key=attacker_key)

    response = await client.get("/api/auth/me", headers=bearer(token))

    assert response.status_code == 401
    assert response.json()["message"] == "Token không hợp lệ."


async def test_me_rejects_expired_token(client: AsyncClient, make_token) -> None:
    token = make_token(uuid4(), expires_in=timedelta(seconds=-1))

    response = await client.get("/api/auth/me", headers=bearer(token))

    assert response.status_code == 401
    assert response.json()["message"] == "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại."


async def test_me_rejects_locked_business_account(
    client: AsyncClient, add_user, make_token
) -> None:
    auth_user_id = uuid4()
    add_user(auth_user_id=auth_user_id, is_active=False)

    response = await client.get("/api/auth/me", headers=bearer(make_token(auth_user_id)))

    assert response.status_code == 401
    assert response.json()["message"] == "Email hoặc mật khẩu không đúng."


async def test_me_returns_404_when_supabase_user_has_no_business_profile(
    client: AsyncClient, make_token
) -> None:
    response = await client.get("/api/auth/me", headers=bearer(make_token(uuid4())))

    assert response.status_code == 404
    assert response.json()["message"] == "Không tìm thấy hồ sơ tài khoản."
