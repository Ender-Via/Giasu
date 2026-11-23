import http.client
import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from functools import lru_cache
from typing import Any, Final, Protocol

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

SIGNED_URL_TTL_SECONDS: Final = 60 * 60
_REQUEST_TIMEOUT_SECONDS: Final = 15


class FileStorageError(Exception):
    pass


class FileStorage(Protocol):
    def upload(self, path: str, data: bytes, content_type: str) -> None: ...

    def delete(self, paths: list[str]) -> None: ...

    def create_signed_urls(self, paths: list[str], expires_in: int) -> dict[str, str]: ...


class SupabaseFileStorage:
    def __init__(self, base_url: str, api_key: str, bucket: str) -> None:
        self._storage_url = f"{base_url.rstrip('/')}/storage/v1"
        self._api_key = api_key
        self._bucket = bucket

    def upload(self, path: str, data: bytes, content_type: str) -> None:
        self._request(
            "POST",
            f"/object/{self._bucket}/{_quote(path)}",
            body=data,
            content_type=content_type,
            extra_headers={"x-upsert": "false"},
        )

    def delete(self, paths: list[str]) -> None:
        if paths:
            self._request("DELETE", f"/object/{self._bucket}", json_body={"prefixes": paths})

    def create_signed_urls(self, paths: list[str], expires_in: int) -> dict[str, str]:
        if not paths:
            return {}
        items = self._request(
            "POST",
            f"/object/sign/{self._bucket}",
            json_body={"expiresIn": expires_in, "paths": paths},
        )
        if not isinstance(items, list):
            raise FileStorageError("Storage trả kết quả ký URL không đúng định dạng.")
        signed: dict[str, str] = {}
        for item in items:
            if isinstance(item, dict) and item.get("signedURL") and not item.get("error"):
                signed[str(item["path"])] = f"{self._storage_url}{item['signedURL']}"
        return signed

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: bytes | None = None,
        content_type: str | None = None,
        json_body: Any = None,
        extra_headers: dict[str, str] | None = None,
    ) -> Any:
        if not self._api_key:
            raise FileStorageError("Chưa cấu hình SUPABASE_SECRET_KEY cho Storage.")
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            content_type = "application/json"

        headers = {"apikey": self._api_key, "Authorization": f"Bearer {self._api_key}"}
        if content_type:
            headers["Content-Type"] = content_type
        headers.update(extra_headers or {})

        request = urllib.request.Request(
            f"{self._storage_url}{path}", data=body, method=method, headers=headers
        )
        try:
            with _OPENER.open(request, timeout=_REQUEST_TIMEOUT_SECONDS) as response:
                raw = response.read()
            return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            logger.error("Storage trả HTTP %s cho %s %s", exc.code, method, path)
            raise FileStorageError(f"Storage trả HTTP {exc.code}.") from exc
        except (OSError, http.client.HTTPException, ValueError) as exc:
            logger.error("Lỗi khi gọi Storage %s %s: %s", method, path, type(exc).__name__)
            raise FileStorageError("Không kết nối được Storage.") from exc


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def _quote(path: str) -> str:
    return urllib.parse.quote(path, safe="/")


def build_file_storage(settings: Settings) -> SupabaseFileStorage:
    secret = settings.supabase_secret_key
    api_key = secret.get_secret_value() if secret is not None else ""
    return SupabaseFileStorage(settings.supabase_url, api_key, settings.supabase_storage_bucket)


@lru_cache
def get_file_storage() -> FileStorage:
    return build_file_storage(get_settings())
