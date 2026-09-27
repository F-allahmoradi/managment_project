"""اسکیمای ورودی ابزارهای اعلان داخل پنل.

هر کس فقط اعلان خودش را می‌بیند. نوع از seed است؛ ابزار lookup جدا نیست.
content_id از کلاینت گرفته نمی‌شود.
"""

from typing import Optional

from pydantic import Field

from schemas.crud.common import IdInput, PaginationInput


class GetNotificationInput(IdInput):
    """ورودی خواندن یک اعلان با شناسه."""


class ListNotificationsInput(PaginationInput):
    """فهرست اعلان‌های خود کاربر جاری."""

    is_read: Optional[bool] = Field(
        default=None,
        description="اگر بیاید فقط خوانده یا نخوانده",
    )


class MarkNotificationReadInput(GetNotificationInput):
    """ورودی علامت‌زدن اعلان به‌عنوان خوانده‌شده."""
