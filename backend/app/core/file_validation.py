import unicodedata
from dataclasses import dataclass
from pathlib import PurePosixPath, PureWindowsPath
from typing import Final

MAX_EVIDENCE_BYTES: Final = 5 * 1024 * 1024
MAX_FILE_NAME_LENGTH: Final = 255

_SIGNATURES: Final = (
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"%PDF-", "application/pdf"),
)
_EXTENSIONS: Final = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".pdf": "application/pdf",
}
STORAGE_EXTENSIONS: Final = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "application/pdf": ".pdf",
}


@dataclass(frozen=True)
class IncomingFile:
    file_name: str
    data: bytes


@dataclass(frozen=True)
class ValidatedFile:
    file_name: str
    content_type: str
    data: bytes

    @property
    def size_bytes(self) -> int:
        return len(self.data)


def clean_file_name(raw_name: str | None) -> str:
    name = unicodedata.normalize("NFC", raw_name or "").strip()
    name = PureWindowsPath(PurePosixPath(name).name).name
    return name[:MAX_FILE_NAME_LENGTH] or "tep-minh-chung"


def detect_content_type(data: bytes) -> str | None:
    for signature, content_type in _SIGNATURES:
        if data.startswith(signature):
            return content_type
    return None


def validate_evidence_file(incoming: IncomingFile) -> tuple[ValidatedFile | None, str | None]:
    name = clean_file_name(incoming.file_name)
    if len(incoming.data) > MAX_EVIDENCE_BYTES:
        return None, f"Tệp '{name}' vượt quá 5 MB."

    detected = detect_content_type(incoming.data)
    by_extension = _EXTENSIONS.get(PurePosixPath(name).suffix.lower())
    if detected is None or detected != by_extension:
        return None, f"Tệp '{name}' không đúng định dạng JPG, PNG hoặc PDF."

    return ValidatedFile(file_name=name, content_type=detected, data=incoming.data), None
