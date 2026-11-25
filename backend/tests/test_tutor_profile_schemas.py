import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from app.schemas.tutor_profiles import AvailabilityRequest, TutorProfileUpsertRequest
from tests.profile_fixtures import valid_profile_payload

FEE = "Học phí từ 50.000 đến 2.000.000 đồng, làm tròn đến nghìn"


def messages_for(**overrides: object) -> list[str]:
    with pytest.raises(ValidationError) as caught:
        TutorProfileUpsertRequest.model_validate(valid_profile_payload(**overrides))
    return [str(error["ctx"]["error"]) for error in caught.value.errors()]


def test_du_lieu_hop_le_duoc_chuan_hoa() -> None:
    data = TutorProfileUpsertRequest.model_validate(
        valid_profile_payload(
            title="  [TEST] Tiếng Anh giao tiếp  ",
            subjectIds=[3, 3, 1],
            teachingWards=[" Phường Bến Thành ", "", "Phường Bến Thành"],
            description="   ",
        )
    )

    assert data.title == "[TEST] Tiếng Anh giao tiếp"
    assert data.subjectIds == [3, 1]
    assert data.teachingWards == ["Phường Bến Thành"]
    assert data.description is None


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"title": "Ngắn quá"}, "Tiêu đề từ 10 đến 150 ký tự"),
        ({"title": "x" * 151}, "Tiêu đề từ 10 đến 150 ký tự"),
        ({"subjectIds": []}, "Chọn từ 1 đến 5 môn"),
        ({"subjectIds": [1, 2, 3, 4, 5, 6]}, "Chọn từ 1 đến 5 môn"),
        ({"subjectIds": ["1"]}, "Chọn từ 1 đến 5 môn"),
        ({"subjectIds": [40_000]}, "Chọn từ 1 đến 5 môn"),
        ({"subjectIds": [0]}, "Chọn từ 1 đến 5 môn"),
        ({"educationLevel": None}, "Vui lòng chọn cấp học"),
        ({"educationLevel": "University"}, "Vui lòng chọn cấp học"),
        ({"teachingMode": ""}, "Vui lòng chọn hình thức dạy"),
        ({"province": " "}, "Vui lòng chọn tỉnh/thành"),
        ({"province": "Quận 1"}, "Tỉnh/thành không hợp lệ"),
        ({"teachingWards": []}, "Nhập ít nhất một phường/xã"),
        ({"teachingWards": [f"Phường {i}" for i in range(6)]}, "Nhập tối đa 5 phường/xã"),
        ({"teachingWards": ["P" * 101]}, "Mỗi phường/xã không quá 100 ký tự"),
        ({"expectedFeePerSession": 49_000}, FEE),
        ({"expectedFeePerSession": 2_001_000}, FEE),
        ({"expectedFeePerSession": 150_500}, FEE),
        ({"expectedFeePerSession": True}, FEE),
        ({"description": "x" * 2001}, "Giới thiệu không quá 2000 ký tự"),
    ],
)
def test_moi_truong_sai_tra_dung_cau_thong_bao(overrides: dict, expected: str) -> None:  # BR-04
    assert messages_for(**overrides) == [expected]


@pytest.mark.parametrize(("title", "fee"), [("x" * 10, 50_000), ("x" * 150, 2_000_000)])
def test_dung_bien_tieu_de_va_hoc_phi_thi_hop_le(title: str, fee: int) -> None:  # BR-04
    data = TutorProfileUpsertRequest.model_validate(
        valid_profile_payload(title=title, expectedFeePerSession=fee)
    )
    assert (data.title, data.expectedFeePerSession) == (title, fee)


def test_chi_day_online_thi_khong_can_phuong_xa_va_bo_gia_tri_cu() -> None:  # BR-04, D37
    data = TutorProfileUpsertRequest.model_validate(
        valid_profile_payload(teachingMode="Online", teachingWards=["Phường cũ"])
    )
    assert data.teachingWards == []


def test_tinh_nhap_dang_dau_to_hop_van_khop_danh_muc() -> None:  # D37
    import unicodedata

    data = TutorProfileUpsertRequest.model_validate(
        valid_profile_payload(province=unicodedata.normalize("NFD", "Đắk Lắk"))
    )
    assert data.province == "Đắk Lắk"


def test_trang_thai_nhan_day_ngoai_ba_gia_tri_thi_loi() -> None:  # AC-PROFILE-09
    with pytest.raises(ValidationError) as caught:
        AvailabilityRequest.model_validate({"availability": "Busy"})
    assert str(caught.value.errors()[0]["ctx"]["error"]) == "Trạng thái nhận dạy không hợp lệ."


@pytest.mark.anyio
async def test_api_tra_400_liet_ke_dung_cac_truong_sai(  # NFR-06
    client: AsyncClient, tutor
) -> None:
    response = await client.post(
        "/api/tutor-profiles",
        json={"title": "abc", "teachingMode": "Offline", "expectedFeePerSession": 10},
        headers=tutor.headers,
    )

    assert response.status_code == 400
    assert response.json()["errors"] == [
        "Tiêu đề từ 10 đến 150 ký tự",
        "Chọn từ 1 đến 5 môn",
        "Vui lòng chọn cấp học",
        "Vui lòng chọn tỉnh/thành",
        "Nhập ít nhất một phường/xã",
        "Học phí từ 50.000 đến 2.000.000 đồng, làm tròn đến nghìn",
    ]


@pytest.mark.anyio
async def test_body_khong_phai_json_thi_400_cau_chung(client: AsyncClient, tutor) -> None:
    response = await client.post(
        "/api/tutor-profiles",
        content=b"{khong-phai-json",
        headers={**tutor.headers, "Content-Type": "application/json"},
    )

    assert response.status_code == 400
    assert response.json()["errors"] == ["Dữ liệu gửi lên không hợp lệ."]
