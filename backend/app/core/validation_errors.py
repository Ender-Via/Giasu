from collections.abc import Iterable
from typing import Any, Final

GENERIC_VALIDATION_MESSAGE: Final = "Dữ liệu gửi lên không hợp lệ."


def collect_validation_messages(errors: Iterable[dict[str, Any]]) -> list[str]:
    messages: list[str] = []
    for error in errors:
        context_error = (error.get("ctx") or {}).get("error")
        if error.get("type") == "value_error" and context_error is not None:
            message = str(context_error)
        else:
            message = GENERIC_VALIDATION_MESSAGE
        if message not in messages:
            messages.append(message)
    return messages or [GENERIC_VALIDATION_MESSAGE]
