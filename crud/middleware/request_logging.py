"""ثبت مدت اجرای هر درخواست CRUD به میلی‌ثانیه.

پیاده‌سازی در logging_module است.
لاگ روی stderr و فایل می‌رود تا stdout مخصوص پروتکل MCP (stdio) بماند.
"""

from logging_module import log_operation as log_duration
from logging_module import setup_logging

__all__ = ["log_duration", "setup_logging"]
