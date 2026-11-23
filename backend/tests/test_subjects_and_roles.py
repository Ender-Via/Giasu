import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_danh_muc_mon_tra_dung_thu_tu_cho_moi_vai_tro(  # BR-24
    client: AsyncClient, make_account, subjects
) -> None:
    for role_id in (1, 2, 3):
        account = make_account(role_id)
        response = await client.get("/api/subjects", headers=account.headers)

        assert response.status_code == 200
        names = [item["name"] for item in response.json()["data"]]
        assert names[:4] == ["Toán", "Tiếng Việt", "Ngữ văn", "Tiếng Anh"]
        assert len(names) == len(subjects)


async def test_danh_muc_mon_khong_co_token_thi_401(client: AsyncClient) -> None:  # AC-AUTH-07
    response = await client.get("/api/subjects")

    assert response.status_code == 401


async def test_sai_vai_tro_goi_api_ho_so_thi_403(  # AC-AUTH-06, BR-SCOPE-05
    client: AsyncClient, make_account, subjects
) -> None:
    for role_id in (1, 3):
        account = make_account(role_id)
        response = await client.get("/api/tutor-profiles/mine", headers=account.headers)

        assert response.status_code == 403
        assert response.json() == {
            "success": False,
            "data": None,
            "message": "Bạn không có quyền thực hiện hành động này.",
            "errors": None,
        }


async def test_tai_khoan_bi_khoa_khong_goi_duoc_api_ho_so(  # D06
    client: AsyncClient, add_user, make_token, subjects
) -> None:
    from uuid import uuid4

    auth_user_id = uuid4()
    add_user(auth_user_id=auth_user_id, role_id=2, is_active=False)

    response = await client.get(
        "/api/tutor-profiles/mine", headers={"Authorization": f"Bearer {make_token(auth_user_id)}"}
    )

    assert response.status_code == 401
