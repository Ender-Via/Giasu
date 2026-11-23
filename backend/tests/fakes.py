from collections.abc import Callable

from app.core.file_storage import FileStorageError

JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"0" * 64
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 64
PDF_BYTES = b"%PDF-1.7\n" + b"0" * 64
DOCX_BYTES = b"PK\x03\x04" + b"0" * 64


class InMemoryFileStorage:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}
        self.deleted: list[str] = []
        self.fail_on_upload_number: int | None = None
        self.fail_signing = False
        self.on_upload: Callable[[], None] | None = None
        self._upload_count = 0

    def upload(self, path: str, data: bytes, content_type: str) -> None:
        self._upload_count += 1
        if self.on_upload is not None:
            self.on_upload()
        if self._upload_count == self.fail_on_upload_number:
            raise FileStorageError("Lỗi Storage giả lập.")
        if path in self.objects:
            raise FileStorageError("Object đã tồn tại.")
        self.objects[path] = (data, content_type)

    def delete(self, paths: list[str]) -> None:
        for path in paths:
            self.objects.pop(path, None)
        self.deleted.extend(paths)

    def create_signed_urls(self, paths: list[str], expires_in: int) -> dict[str, str]:
        if self.fail_signing:
            raise FileStorageError("Lỗi ký URL giả lập.")
        return {
            path: f"https://storage.test/{path}?expiresIn={expires_in}"
            for path in paths
            if path in self.objects
        }
