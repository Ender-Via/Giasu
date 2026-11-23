from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def as_utc_or_none(value: datetime | None) -> datetime | None:
    return as_utc(value) if value is not None else None
