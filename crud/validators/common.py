"""کمک‌های تکراری اعتبارسنجی؛ اسکیمای هر جدول همچنان جداست."""

from __future__ import annotations


def parse_id(model_cls, row_id: int) -> int:
    """شناسه را با اسکیمای همان جدول بررسی می‌کند."""
    return model_cls(id=row_id).id


def parse_page(model_cls, limit=None, offset=None) -> tuple[int, int]:
    """صفحه‌بندی را با اسکیما بررسی می‌کند؛ None یعنی پیش‌فرض مدل."""
    payload = {}
    if limit is not None:
        payload["limit"] = limit
    if offset is not None:
        payload["offset"] = offset
    parsed = model_cls(**payload)
    return parsed.limit, parsed.offset


def parse_optional(model_cls, **fields) -> dict:
    """مدل را فقط با فیلدهای غیرNone می‌سازد و dump می‌کند."""
    payload = {key: value for key, value in fields.items() if value is not None}
    return model_cls(**payload).model_dump()


def writable_update(parsed) -> dict:
    """id را نگه می‌دارد و فیلدهای None را از به‌روزرسانی برمی‌دارد."""
    dumped = parsed.model_dump()
    return {
        "id": dumped["id"],
        **{
            key: value
            for key, value in dumped.items()
            if key != "id" and value is not None
        },
    }
