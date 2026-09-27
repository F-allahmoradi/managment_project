"""خواندن نام وضعیت‌ها و آستانه‌ها از config/columns.yaml.

عدد آمار از SQL است؛ این فایل فقط برچسب seed و حد هشدار را می‌دهد.
"""

from pathlib import Path

import yaml

from logging_module import logged_step

_ROOT = Path(__file__).resolve().parent.parent
_DEFAULTS = {
    "task_statuses": {"completed": "تکمیل شده", "cancelled": "لغو شده"},
    "project_statuses": {"completed": "تکمیل شده", "cancelled": "لغو شده"},
    "thresholds": {"repeated_follow_ups": 3, "at_risk_overdue_tasks": 1},
    "pagination": {"default_limit": 10, "max_limit": 50, "default_offset": 0},
}


def _merge_section(raw, key: str) -> dict:
    merged = dict(_DEFAULTS[key])
    if isinstance(raw, dict) and isinstance(raw.get(key), dict):
        merged.update(raw[key])
    return merged


def load_stats_config() -> dict:
    """تنظیم وضعیت‌ها و آستانه‌های آمار را از YAML می‌خواند."""
    path = _ROOT / "config/columns.yaml"
    raw = None
    if path.exists():
        with path.open(encoding="utf-8") as handle:
            raw = yaml.safe_load(handle)
    return {
        "task_statuses": _merge_section(raw, "task_statuses"),
        "project_statuses": _merge_section(raw, "project_statuses"),
        "thresholds": _merge_section(raw, "thresholds"),
        "pagination": _merge_section(raw, "pagination"),
    }


def completed_task_status() -> str:
    return str(load_stats_config()["task_statuses"]["completed"])


def cancelled_task_status() -> str:
    return str(load_stats_config()["task_statuses"]["cancelled"])


def completed_project_status() -> str:
    return str(load_stats_config()["project_statuses"]["completed"])


def cancelled_project_status() -> str:
    return str(load_stats_config()["project_statuses"]["cancelled"])


def repeated_follow_up_threshold() -> int:
    return int(load_stats_config()["thresholds"]["repeated_follow_ups"])


def at_risk_overdue_threshold() -> int:
    return int(load_stats_config()["thresholds"]["at_risk_overdue_tasks"])


load_stats_config = logged_step("load")(load_stats_config)
