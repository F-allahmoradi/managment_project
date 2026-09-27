"""کاتالوگ و نمای قابلیتی هر MCP؛ ابزار جدا برای هر tool نیست."""

from pathlib import Path

from errors.crud import format_error, format_success
from playground.loaders import call_symbol, load_symbol
from playground.samples import SAMPLE_QUERIES

REPO_ROOT = Path(__file__).resolve().parents[2]

SECTIONS = (
    {
        "id": "embedding",
        "server": "management-embedding",
        "title": "امبدینگ",
        "blurb": "تحلیل ذخیره‌شده را برداری کن و با سؤال، موارد مشابه را از متن خام و فکت استخراج‌شده پیدا کن.",
        "ui": "embedding",
    },
    {
        "id": "ner",
        "server": "management-ner",
        "title": "استخراج",
        "blurb": "متن پیام یا جلسه را یک‌بار استخراج کن؛ موجودیت، موضوع، احساس، ژانر و نیت با هم می‌آیند.",
        "ui": "extract",
    },
    {
        "id": "crud",
        "server": "management-crud",
        "title": "CRUD",
        "blurb": "نمای پروژه‌ها، پیام‌ها و تحلیل‌های متن بازیگر جاری. فرم جدا برای هر موجودیت نیست.",
        "ui": "snapshot",
    },
    {
        "id": "meeting",
        "server": "management-meeting",
        "title": "جلسه",
        "blurb": "جلسات قابل‌مشاهدهٔ بازیگر جاری.",
        "ui": "snapshot",
    },
    {
        "id": "finance",
        "server": "management-finance",
        "title": "مالی",
        "blurb": "حساب‌ها و تراکنش‌های اخیر.",
        "ui": "snapshot",
    },
    {
        "id": "stats",
        "server": "management-stats",
        "title": "آمار",
        "blurb": "پروژه‌های در معرض تأخیر و وظایف عقب‌افتاده.",
        "ui": "snapshot",
    },
    {
        "id": "reminder",
        "server": "management-reminder",
        "title": "یادآوری",
        "blurb": "یادآوری‌های قابل‌مشاهدهٔ بازیگر جاری.",
        "ui": "snapshot",
    },
    {
        "id": "nlp",
        "server": "management-nlp",
        "title": "پردازش زبانی",
        "blurb": "فکت عددی، علت، نقل‌قول و قاب مسئله با شاهد داخل متن. نیت و ژانر در استخراج است.",
        "ui": "nlp-extract",
    },
)

_ROOTS = {
    "ner": REPO_ROOT / "ner",
    "nlp": REPO_ROOT / "nlp",
    "crud": REPO_ROOT / "crud",
    "meeting": REPO_ROOT / "meeting",
    "finance": REPO_ROOT / "finance",
    "stats": REPO_ROOT / "stats",
    "reminder": REPO_ROOT / "reminder",
}


def catalog() -> dict:
    """فهرست بخش‌های صفحه را برمی‌گرداند."""
    return format_success("بخش‌های MCP", sections=list(SECTIONS))


def _run(package: str, dotted_module: str, symbol: str, **kwargs) -> dict:
    """ابزار یک سرور دیگر را داخل isolation همان پوشه صدا می‌زند."""
    return call_symbol(_ROOTS[package], dotted_module, symbol, **kwargs)


def _group(title: str, packed: dict) -> dict:
    """خروجی فهرست را به یک گروه نمایش تبدیل می‌کند."""
    if packed.get("status") != "success":
        return {
            "title": title,
            "error": packed.get("message") or "خواندن ناموفق بود",
            "records": [],
        }
    return {
        "title": title,
        "message": packed.get("message"),
        "records": packed.get("records") or [],
    }


def _safe_group(title: str, runner) -> dict:
    """شکست یک گروه بقیهٔ نما را دور نمی‌ریزد."""
    try:
        return _group(title, runner())
    except Exception as exc:
        packed = format_error(exc)
        return {
            "title": title,
            "error": packed.get("message") or "خواندن ناموفق بود",
            "records": [],
        }


def _snapshot_crud() -> dict:
    groups = [
        _safe_group(
            "پروژه‌ها",
            lambda: _run(
                "crud",
                "mcp_server.tools.project.list_projects",
                "run_list_projects",
                limit=10,
                offset=0,
            ),
        ),
        _safe_group(
            "پیام‌ها",
            lambda: _run(
                "crud",
                "mcp_server.tools.message.list_messages",
                "run_list_messages",
                limit=10,
                offset=0,
            ),
        ),
        _safe_group(
            "تحلیل‌های متن",
            lambda: _run(
                "crud",
                "mcp_server.tools.text_analysis.list_text_analyses",
                "run_list_text_analyses",
                limit=10,
                offset=0,
            ),
        ),
    ]
    return format_success("نمای CRUD", groups=groups)


def _snapshot_meeting() -> dict:
    groups = [
        _safe_group(
            "جلسات",
            lambda: _run(
                "meeting",
                "mcp_server.tools.meeting.list_meetings",
                "run_list_meetings",
                limit=10,
                offset=0,
            ),
        ),
    ]
    return format_success("نمای جلسه", groups=groups)


def _snapshot_finance() -> dict:
    groups = [
        _safe_group(
            "حساب‌ها",
            lambda: _run(
                "finance",
                "mcp_server.tools.financial_account.list_financial_accounts",
                "run_list_financial_accounts",
                limit=10,
                offset=0,
            ),
        ),
        _safe_group(
            "تراکنش‌ها",
            lambda: _run(
                "finance",
                "mcp_server.tools.financial_transaction.list_financial_transactions",
                "run_list_financial_transactions",
                limit=10,
                offset=0,
            ),
        ),
    ]
    return format_success("نمای مالی", groups=groups)


def _snapshot_stats() -> dict:
    groups = [
        _safe_group(
            "پروژه‌های در معرض تأخیر",
            lambda: _run(
                "stats",
                "mcp_server.tools.project.list_at_risk_projects",
                "run_list_at_risk_projects",
                limit=10,
                offset=0,
            ),
        ),
        _safe_group(
            "وظایف عقب‌افتاده",
            lambda: _run(
                "stats",
                "mcp_server.tools.task.get_overdue_tasks",
                "run_get_overdue_tasks",
                limit=10,
                offset=0,
            ),
        ),
    ]
    return format_success("نمای آمار", groups=groups)


def _snapshot_reminder() -> dict:
    groups = [
        _safe_group(
            "یادآوری‌ها",
            lambda: _run(
                "reminder",
                "mcp_server.tools.reminder.list_reminders",
                "run_list_reminders",
                limit=10,
                offset=0,
            ),
        ),
    ]
    return format_success("نمای یادآوری", groups=groups)


_SNAPSHOTS = {
    "crud": _snapshot_crud,
    "meeting": _snapshot_meeting,
    "finance": _snapshot_finance,
    "stats": _snapshot_stats,
    "reminder": _snapshot_reminder,
}


def snapshot(mcp_id: str) -> dict:
    """نمای قابلیتی یک MCP را می‌خواند."""
    runner = _SNAPSHOTS.get(mcp_id)
    if runner is None:
        return {
            "status": "error",
            "error_code": "NOT_FOUND",
            "message": "این بخش نمای فهرستی ندارد",
        }
    try:
        return runner()
    except Exception as exc:
        return format_error(exc)


def load_sample() -> dict:
    """متن نمونهٔ استخراج را از NER می‌آورد."""
    text = load_symbol(_ROOTS["ner"], "tests.sample", "SAMPLE_TEXT")
    return format_success(
        "متن ساختگی است؛ از دیتابیس نیامده.",
        text=text,
    )


def extract_text(text: str) -> dict:
    """شش لایهٔ استخراج را یک‌بار اجرا می‌کند؛ ابزار جدا برای هر لایه نیست."""
    return call_symbol(_ROOTS["ner"], "playground.app", "_dump_all", text=text)


def load_nlp_sample() -> dict:
    """متن نمونهٔ فکت و قاب را از NLP می‌آورد."""
    text = load_symbol(_ROOTS["nlp"], "tests.sample", "SAMPLE_TEXT")
    return format_success(
        "متن ساختگی است؛ از دیتابیس نیامده.",
        text=text,
    )


def extract_nlp(text: str) -> dict:
    """فکت، نقل‌قول و قاب مسئله را یک‌بار اجرا می‌کند. INSERT نیست."""
    return call_symbol(_ROOTS["nlp"], "playground.app", "_dump_all", text=text)


def load_search_samples() -> dict:
    """سؤال‌های آمادهٔ تست جستجوی معنایی را می‌دهد."""
    return format_success(
        "اول تحلیل را امبد کن، بعد یکی از سؤال‌ها را بزن.",
        samples=list(SAMPLE_QUERIES),
    )
