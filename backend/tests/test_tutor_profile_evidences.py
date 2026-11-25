import pytest
from httpx import AsyncClient

from tests.fakes import DOCX_BYTES, JPEG_BYTES, PDF_BYTES, PNG_BYTES

pytestmark = pytest.mark.anyio

FIVE_MB = 5 * 1024 * 1024


def evidence_url(profile_id: str) -> str:
    return f"/api/tutor-profiles/{profile_id}/evidences"


async def test_co_4_minh_chung_tai_them_1_duoc_tai_tiep_thi_409(  # AC-PROFILE-05, BR-03
    client: AsyncClient, tutor, create_profile, storage
) -> None:
    profile = await create_profile(tutor)
    four = [("files", (f"giay-khen-{i}.png", PNG_BYTES, "image/png")) for i in range(4)]
    await client.post(evidence_url(profile["id"]), files=four, headers=tutor.headers)

    fifth = await client.post(
        evidence_url(profile["id"]),
        files={"files": ("bang-diem.pdf", PDF_BYTES, "application/pdf")},
        headers=tutor.headers,
    )
    sixth = await client.post(
        evidence_url(profile["id"]),
        files={"files": ("chung-chi.jpg", JPEG_BYTES, "image/jpeg")},
        headers=tutor.headers,
    )

    assert fifth.status_code == 201
    assert fifth.json()["data"][0]["contentType"] == "application/pdf"
    assert sixth.status_code == 409
    detail = await client.get(f"/api/tutor-profiles/{profile['id']}", headers=tutor.headers)
    assert detail.json()["data"]["evidenceCount"] == 5
    assert len(storage.objects) == 5


@pytest.mark.parametrize(
    ("name", "content", "expected"),
    [
        ("the-sv.docx", DOCX_BYTES, "Tệp 'the-sv.docx' không đúng định dạng JPG, PNG hoặc PDF."),
        ("anh.pdf", JPEG_BYTES, "Tệp 'anh.pdf' không đúng định dạng JPG, PNG hoặc PDF."),
        ("rong.png", b"", "Tệp 'rong.png' không đúng định dạng JPG, PNG hoặc PDF."),
        ("lon.pdf", b"%PDF-" + b"0" * FIVE_MB, "Tệp 'lon.pdf' vượt quá 5 MB."),
    ],
    ids=["docx", "duoi-khong-khop", "tep-rong", "qua-5mb"],
)
async def test_tep_sai_dinh_dang_hoac_qua_5mb_thi_400_khong_len_storage(  # BR-03, D16
    client: AsyncClient, tutor, create_profile, storage, name: str, content: bytes, expected: str
) -> None:
    profile = await create_profile(tutor)

    response = await client.post(
        evidence_url(profile["id"]),
        files={"files": (name, content, "application/octet-stream")},
        headers=tutor.headers,
    )

    assert response.status_code == 400
    assert response.json()["errors"] == [expected]
    assert storage.objects == {}


async def test_dung_5mb_thi_hop_le(client: AsyncClient, tutor, create_profile) -> None:  # BR-03
    profile = await create_profile(tutor)
    exact = b"%PDF-" + b"0" * (FIVE_MB - 5)

    response = await client.post(
        evidence_url(profile["id"]),
        files={"files": ("vua-du.pdf", exact, "application/pdf")},
        headers=tutor.headers,
    )

    assert response.status_code == 201
    assert response.json()["data"][0]["sizeBytes"] == FIVE_MB


async def test_khong_chon_tep_thi_400_qua_5_tep_mot_luot_thi_409(  # FR-04
    client: AsyncClient, tutor, create_profile, storage
) -> None:
    profile = await create_profile(tutor)
    six = [("files", (f"anh-{i}.png", PNG_BYTES, "image/png")) for i in range(6)]

    empty = await client.post(evidence_url(profile["id"]), headers=tutor.headers)
    too_many = await client.post(evidence_url(profile["id"]), files=six, headers=tutor.headers)

    assert empty.status_code == 400
    assert empty.json()["errors"] == ["Chọn từ 1 đến 5 tệp minh chứng."]
    assert too_many.status_code == 409
    assert storage.objects == {}


async def test_ho_so_bi_gui_duyet_trong_luc_dang_tai_thi_409_va_don_tep(  # BR-26, NFR-03
    client: AsyncClient, tutor, create_profile, storage, set_status
) -> None:
    profile = await create_profile(tutor)
    storage.on_upload = lambda: set_status(profile["id"], "PendingReview")

    response = await client.post(
        evidence_url(profile["id"]),
        files={"files": ("bang-diem.pdf", PDF_BYTES, "application/pdf")},
        headers=tutor.headers,
    )

    assert response.status_code == 409
    assert storage.objects == {}
    assert len(storage.deleted) == 1


async def test_storage_loi_giua_chung_thi_khong_luu_ban_ghi_va_don_tep(  # NFR-03
    client: AsyncClient, tutor, create_profile, storage
) -> None:
    profile = await create_profile(tutor)
    storage.fail_on_upload_number = 2
    two = [("files", (f"anh-{i}.png", PNG_BYTES, "image/png")) for i in range(2)]

    response = await client.post(evidence_url(profile["id"]), files=two, headers=tutor.headers)

    assert response.status_code == 500
    assert storage.objects == {}
    assert len(storage.deleted) == 1
    detail = await client.get(f"/api/tutor-profiles/{profile['id']}", headers=tutor.headers)
    assert detail.json()["data"]["evidenceCount"] == 0


async def test_go_minh_chung_xoa_ban_ghi_va_tep(  # BR-26, CC-05
    client: AsyncClient, tutor, create_profile, storage
) -> None:
    profile = await create_profile(tutor)
    uploaded = await client.post(
        evidence_url(profile["id"]),
        files={"files": ("bang-diem.pdf", PDF_BYTES, "application/pdf")},
        headers=tutor.headers,
    )
    evidence_id = uploaded.json()["data"][0]["id"]

    removed = await client.delete(
        f"{evidence_url(profile['id'])}/{evidence_id}", headers=tutor.headers
    )
    again = await client.delete(
        f"{evidence_url(profile['id'])}/{evidence_id}", headers=tutor.headers
    )

    assert removed.status_code == 200
    assert again.status_code == 404
    assert again.json()["message"] == "Không tìm thấy minh chứng."
    assert storage.objects == {}


async def test_go_minh_chung_khi_cho_duyet_thi_409(  # BR-26
    client: AsyncClient, tutor, create_profile, set_status
) -> None:
    profile = await create_profile(tutor)
    uploaded = await client.post(
        evidence_url(profile["id"]),
        files={"files": ("bang-diem.pdf", PDF_BYTES, "application/pdf")},
        headers=tutor.headers,
    )
    set_status(profile["id"], "PendingReview")

    response = await client.delete(
        f"{evidence_url(profile['id'])}/{uploaded.json()['data'][0]['id']}", headers=tutor.headers
    )

    assert response.status_code == 409


async def test_minh_chung_cua_ho_so_nguoi_khac_tra_404(  # BR-SCOPE-02, D07
    client: AsyncClient, tutor, other_tutor, create_profile, storage
) -> None:
    profile = await create_profile(other_tutor)

    upload = await client.post(
        evidence_url(profile["id"]),
        files={"files": ("bang-diem.pdf", PDF_BYTES, "application/pdf")},
        headers=tutor.headers,
    )

    assert upload.status_code == 404
    assert upload.json()["message"] == "Không tìm thấy hồ sơ."
    assert storage.objects == {}
