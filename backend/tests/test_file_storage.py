import http.client
import io
import json
import urllib.error
import urllib.request

import pytest
from pydantic import SecretStr

from app.core import file_storage
from app.core.config import Settings
from app.core.file_storage import FileStorageError, SupabaseFileStorage, build_file_storage


class FakeResponse(io.BytesIO):
    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class Captured(list[urllib.request.Request]):
    def __init__(self) -> None:
        super().__init__()
        self.replies: list[bytes] = []


@pytest.fixture
def captured(monkeypatch: pytest.MonkeyPatch) -> Captured:
    requests = Captured()

    def fake_open(request: urllib.request.Request, timeout: float) -> FakeResponse:
        assert timeout > 0
        requests.append(request)
        return FakeResponse(requests.replies.pop(0) if requests.replies else b"")

    monkeypatch.setattr(file_storage._OPENER, "open", fake_open)
    return requests


def fail_with(monkeypatch: pytest.MonkeyPatch, error: BaseException) -> None:
    def failing_open(request: urllib.request.Request, timeout: float) -> None:
        raise error

    monkeypatch.setattr(file_storage._OPENER, "open", failing_open)


def make_storage() -> SupabaseFileStorage:
    return SupabaseFileStorage("https://abc.supabase.co/", "sb_secret_test", "evidences")


def test_upload_gui_dung_bucket_header_va_noi_dung(captured: Captured) -> None:
    make_storage().upload("tutor-profiles/p1/e1.pdf", b"%PDF-1.7", "application/pdf")

    request = captured[0]
    assert request.get_method() == "POST"
    assert request.full_url == (
        "https://abc.supabase.co/storage/v1/object/evidences/tutor-profiles/p1/e1.pdf"
    )
    assert request.get_header("Apikey") == "sb_secret_test"
    assert request.get_header("Authorization") == "Bearer sb_secret_test"
    assert request.get_header("Content-type") == "application/pdf"
    assert request.get_header("X-upsert") == "false"
    assert request.data == b"%PDF-1.7"


def test_ky_url_hang_loat_tra_url_day_du_theo_duong_dan(captured: Captured) -> None:
    captured.replies.append(
        json.dumps(
            [
                {
                    "path": "a.pdf",
                    "signedURL": "/object/sign/evidences/a.pdf?token=t1",
                    "error": None,
                },
                {"path": "b.png", "signedURL": None, "error": "Either the object does not exist"},
            ]
        ).encode()
    )

    urls = make_storage().create_signed_urls(["a.pdf", "b.png"], 3600)

    assert urls == {
        "a.pdf": "https://abc.supabase.co/storage/v1/object/sign/evidences/a.pdf?token=t1"
    }
    assert json.loads(captured[0].data) == {"expiresIn": 3600, "paths": ["a.pdf", "b.png"]}
    assert captured[0].full_url.endswith("/storage/v1/object/sign/evidences")


def test_xoa_gui_danh_sach_prefixes(captured: Captured) -> None:
    make_storage().delete(["a.pdf"])
    make_storage().delete([])

    assert len(captured) == 1
    assert captured[0].get_method() == "DELETE"
    assert json.loads(captured[0].data) == {"prefixes": ["a.pdf"]}


def test_loi_http_doi_thanh_file_storage_error(monkeypatch: pytest.MonkeyPatch) -> None:
    error = urllib.error.HTTPError("https://abc", 403, "Forbidden", {}, None)  # type: ignore[arg-type]
    fail_with(monkeypatch, error)

    with pytest.raises(FileStorageError, match="HTTP 403"):
        make_storage().upload("a.pdf", b"%PDF-", "application/pdf")


@pytest.mark.parametrize(
    "error",
    [ConnectionResetError(), http.client.IncompleteRead(b""), TimeoutError()],
    ids=["mat-ket-noi", "doc-thieu", "het-gio"],
)
def test_loi_mang_giua_chung_cung_thanh_file_storage_error(
    monkeypatch: pytest.MonkeyPatch, error: BaseException
) -> None:
    fail_with(monkeypatch, error)

    with pytest.raises(FileStorageError):
        make_storage().create_signed_urls(["a.pdf"], 3600)


def test_json_hong_thanh_file_storage_error(captured: Captured) -> None:
    captured.replies.append(b"<html>gateway</html>")

    with pytest.raises(FileStorageError):
        make_storage().create_signed_urls(["a.pdf"], 3600)


def test_khong_di_theo_redirect_de_khong_lo_khoa() -> None:
    handler = file_storage._NoRedirect()
    request = urllib.request.Request("https://abc.supabase.co/storage/v1/object/x")

    redirected = handler.redirect_request(
        request, None, 302, "Found", {}, "https://evil.example/steal"
    )

    assert redirected is None


def test_chua_cau_hinh_khoa_thi_khong_goi_storage(captured: Captured) -> None:
    storage = build_file_storage(Settings(_env_file=None, supabase_secret_key=SecretStr("")))

    with pytest.raises(FileStorageError, match="SUPABASE_SECRET_KEY"):
        storage.upload("a.pdf", b"%PDF-", "application/pdf")
    assert captured == []
