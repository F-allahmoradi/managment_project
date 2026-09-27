"""نرمال‌سازی متن فارسی قبل از استخراج موجودیت."""

import re

from logging_module import logged_step

_PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def clean_text(text: str) -> str:
    """رقم فارسی را لاتین می‌کند و فاصله و ی/ک را یکدست می‌کند."""
    cleaned = text.translate(_PERSIAN_DIGITS)
    cleaned = cleaned.replace("\u00a0", " ")
    cleaned = cleaned.replace("ي", "ی").replace("ك", "ک")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    return cleaned.strip()


@logged_step("normalize")
def normalize_text(text: str, number_words: dict | None = None) -> str:
    """رقم فارسی را لاتین می‌کند و فاصله را یکدست می‌کند."""
    del number_words
    return clean_text(text)


def normalize_name(value: str) -> str:
    """نام canonical را برای تطبیق ذکرهای هم‌معنی یکدست می‌کند."""
    cleaned = clean_text(value)
    cleaned = cleaned.replace("\u200c", " ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def find_span(text: str, fragment: str) -> tuple[int, int] | None:
    """جایگاه تکه را در متن پیدا می‌کند."""
    if not fragment:
        return None
    start = text.find(fragment)
    if start < 0:
        return None
    return start, start + len(fragment)
