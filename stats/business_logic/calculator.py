"""محاسبهٔ درصد و برچسب سلامت از شمارش SQL.

پیش‌بینی احتمال تأخیر اینجا نیست؛ فقط نسبت و آستانه.
"""

from logging_module import logged_step


HEALTH_OK = "سالم"
HEALTH_AT_RISK = "در معرض تأخیر"
HEALTH_DELAYED = "تأخیر"


def progress_percent(completed_count: int, task_count: int) -> float:
    """درصد وظایف تکمیل‌شده نسبت به کل وظایف همان پروژه."""
    if task_count <= 0:
        return 0.0
    return round(100.0 * completed_count / task_count, 2)


def completion_rate(completed_count: int, counted_total: int) -> float:
    """نرخ تکمیل نسبت به مخرج داده‌شده (معمولاً کل وظایف)."""
    return progress_percent(completed_count, counted_total)


def health_label(
    overdue_count: int,
    days_remaining,
    project_status: str,
    completed_project_status: str,
    cancelled_project_status: str,
) -> str:
    """برچسب سلامت را از تأخیر وظیفه و مهلت پروژه می‌سازد."""
    if project_status == cancelled_project_status:
        return cancelled_project_status
    if project_status == completed_project_status:
        return HEALTH_OK
    if days_remaining is not None and days_remaining < 0:
        return HEALTH_DELAYED
    if overdue_count > 0:
        return HEALTH_AT_RISK
    return HEALTH_OK


def is_at_risk(label: str) -> bool:
    """اگر پروژه در معرض تأخیر یا تأخیر باشد True است."""
    return label in {HEALTH_AT_RISK, HEALTH_DELAYED}


progress_percent = logged_step("calculate")(progress_percent)
completion_rate = logged_step("calculate")(completion_rate)
health_label = logged_step("calculate")(health_label)
