"""تبدیل تاریخ ذکر TIME به occurred_at.

مدل گاهی ISO می‌دهد و گاهی نمی‌دهد؛ تبدیل از شاهد فارسی اینجا قطعی است.
"""

from datetime import datetime
import re
from typing import Any

from business_logic.normalizer import clean_text

_MONTHS = {
    "فروردین": 1,
    "اردیبهشت": 2,
    "خرداد": 3,
    "تیر": 4,
    "مرداد": 5,
    "شهریور": 6,
    "مهر": 7,
    "آبان": 8,
    "آذر": 9,
    "دی": 10,
    "بهمن": 11,
    "اسفند": 12,
}

_JALALI_RE = re.compile(
    r"(?P<day>\d{1,2})\s+"
    r"(?P<month>فروردین|اردیبهشت|خرداد|تیر|مرداد|شهریور|مهر|آبان|آذر|دی|بهمن|اسفند)"
    r"\s+(?P<year>\d{2,4})"
    r"(?:.*?ساعت\s+(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?)?",
    re.DOTALL,
)
_ISO_RE = re.compile(
    r"(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})"
    r"(?:[ T](?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?(?::(?P<second>\d{2}))?)?"
)


def jalali_to_gregorian(year: int, month: int, day: int) -> tuple[int, int, int]:
    """سال/ماه/روز شمسی را به میلادی تبدیل می‌کند."""
    jy = year - 979
    jm = month - 1
    jd = day - 1
    j_day_no = 365 * jy + (jy // 33) * 8 + (jy % 33 + 3) // 4
    for index in range(jm):
        j_day_no += 31 if index < 6 else 30
    j_day_no += jd
    g_day_no = j_day_no + 79
    gy = 1600 + 400 * (g_day_no // 146097)
    g_day_no %= 146097
    leap = True
    if g_day_no >= 36525:
        g_day_no -= 1
        gy += 100 * (g_day_no // 36524)
        g_day_no %= 36524
        if g_day_no >= 365:
            g_day_no += 1
        else:
            leap = False
    gy += 4 * (g_day_no // 1461)
    g_day_no %= 1461
    if g_day_no >= 366:
        leap = False
        g_day_no -= 1
        gy += g_day_no // 365
        g_day_no %= 365
    gd = g_day_no + 1
    lengths = [0, 31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 1
    for index in range(1, 13):
        size = lengths[index]
        if gd <= size:
            gm = index
            break
        gd -= size
    return gy, gm, gd


def _format(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> str:
    """تاریخ را به رشتهٔ بدون منطقه زمانی می‌نویسد."""
    return datetime(year, month, day, hour, minute, 0).isoformat(sep=" ", timespec="seconds")


def _from_iso(text: str) -> str | None:
    """اگر رشته ISO باشد نگه می‌دارد."""
    raw = text.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        match = _ISO_RE.search(text)
        if not match:
            return None
        hour = int(match.group("hour") or 0)
        minute = int(match.group("minute") or 0)
        return _format(
            int(match.group("year")),
            int(match.group("month")),
            int(match.group("day")),
            hour,
            minute,
        )
    return parsed.replace(tzinfo=None).isoformat(sep=" ", timespec="seconds")


def _from_jalali(text: str) -> str | None:
    """تاریخ شمسی داخل متن را اگر کامل باشد تبدیل می‌کند."""
    match = _JALALI_RE.search(text)
    if match is None:
        return None
    year = int(match.group("year"))
    if year < 100:
        year += 1400
    month = _MONTHS[match.group("month")]
    day = int(match.group("day"))
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return None
    hour = int(match.group("hour") or 0)
    minute = int(match.group("minute") or 0)
    gy, gm, gd = jalali_to_gregorian(year, month, day)
    return _format(gy, gm, gd, hour, minute)


def parse_occurred_at(*values: Any) -> str | None:
    """اولین تاریخ قابل‌تبدیل را از شاهد، canonical یا ISO مدل برمی‌دارد."""
    for value in values:
        if not isinstance(value, str) or not value.strip():
            continue
        text = clean_text(value)
        parsed = _from_jalali(text) or _from_iso(text)
        if parsed:
            return parsed
    return None
