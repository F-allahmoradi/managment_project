"""تقویم هفتهٔ ایرانی برای الگوی جلسه.

۰=شنبه تا ۶=جمعه. تداخل و پیشنهاد هفتهٔ بعد در کد است، نه در دیتابیس.
"""

from datetime import date, datetime, time, timedelta

DAY_NAMES = {
    0: "شنبه",
    1: "یکشنبه",
    2: "دوشنبه",
    3: "سه‌شنبه",
    4: "چهارشنبه",
    5: "پنجشنبه",
    6: "جمعه",
}

_DAY_ALIASES = {
    "شنبه": 0,
    "یکشنبه": 1,
    "دوشنبه": 2,
    "سه‌شنبه": 3,
    "سه شنبه": 3,
    "سهشنبه": 3,
    "چهارشنبه": 4,
    "چهار شنبه": 4,
    "پنجشنبه": 5,
    "پنج شنبه": 5,
    "جمعه": 6,
}


def parse_day_of_week(day_of_week=None, day_name=None) -> int:
    """عدد ۰ تا ۶ یا نام فارسی روز را به day_of_week اسکیما تبدیل می‌کند."""
    if day_of_week is not None:
        value = int(day_of_week)
        if value not in DAY_NAMES:
            raise ValueError("روز هفته باید بین ۰ و ۶ باشد")
        return value
    if not day_name:
        raise ValueError("روز هفته با عدد یا نام لازم است")
    key = " ".join(str(day_name).strip().split())
    if key not in _DAY_ALIASES:
        raise ValueError(f"روز هفته «{day_name}» نامعتبر است")
    return _DAY_ALIASES[key]


def iranian_weekday(value: date) -> int:
    """روز هفتهٔ ایرانی را برمی‌گرداند؛ شنبه=۰."""
    return (value.weekday() + 2) % 7


def week_start_saturday(value: date) -> date:
    """شنبهٔ همان هفتهٔ ایرانی را برمی‌گرداند."""
    return value - timedelta(days=iranian_weekday(value))


def as_time(value) -> time:
    """time یا رشتهٔ HH:MM را به datetime.time تبدیل می‌کند."""
    if isinstance(value, time):
        return value.replace(tzinfo=None)
    if isinstance(value, datetime):
        return value.time()
    text = str(value)
    if len(text) == 5:
        text = text + ":00"
    return time.fromisoformat(text[:8])


def occurrence_in_week(
    day_of_week: int,
    start_time,
    duration_minutes: int,
    weeks_ahead: int,
    now: datetime,
) -> tuple[datetime, datetime]:
    """شروع و پایان جلسه را در هفتهٔ هدف می‌سازد.

    weeks_ahead=0 همین هفته است، ۱ هفتهٔ بعد.
    """
    saturday = week_start_saturday(now.date()) + timedelta(weeks=weeks_ahead)
    target = saturday + timedelta(days=day_of_week)
    start = datetime.combine(target, as_time(start_time))
    end = start + timedelta(minutes=duration_minutes)
    return start, end


def shift_weeks(start: datetime, duration_minutes: int, weeks: int = 1) -> tuple[datetime, datetime]:
    """همان روز و ساعت را به تعداد هفته جلو می‌برد."""
    nxt = start + timedelta(weeks=weeks)
    return nxt, nxt + timedelta(minutes=duration_minutes)


def isoformat_naive(value: datetime) -> str:
    """timestamp بدون منطقه را برای JSON آماده می‌کند."""
    return value.replace(microsecond=0).isoformat()
