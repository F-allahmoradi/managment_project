"""راه‌اندازی لاگر MCP روی stderr و فایل.

stdout کانال JSON-RPC است؛ لاگ هرگز آنجا نمی‌رود.
"""

import logging
from logging.handlers import RotatingFileHandler
import sys

from logging_module.config import load_logging_config, resolve_log_path

LOGGER_NAME = "mcp"
_logger = logging.getLogger(LOGGER_NAME)
_FORMAT = "%(asctime)s %(levelname)s %(message)s"


def reset_logging() -> None:
    """همهٔ handlerهای لاگر MCP را برمی‌دارد.

    ورودی:
        هیچ.
    خروجی:
        هیچ. اثر جانبی روی logging است.
    فراخوانی‌ها:
        Handler.close.
    علت:
        تست باید بتواند فایل و کنسول را از نو ببندد بدون نشت handler.
    """
    for handler in list(_logger.handlers):
        _logger.removeHandler(handler)
        handler.close()
    _logger.setLevel(logging.NOTSET)
    _logger.propagate = False


def setup_logging(config: dict | None = None) -> logging.Logger:
    """لاگر MCP را روی stderr و در صورت تنظیم روی فایل می‌گذارد.

    ورودی:
        config: تنظیم کامل؛ اگر None باشد از logging.yaml خوانده می‌شود.
    خروجی:
        همان logger با نام mcp.
    فراخوانی‌ها:
        load_logging_config، logging.StreamHandler، RotatingFileHandler.
    علت:
        یک‌بار در شروع سرور کافی است؛ تکرار صدا بی‌اثر است مگر بعد از reset.
    """
    if _logger.handlers:
        return _logger
    settings = config if config is not None else load_logging_config()
    level_name = str(settings.get("level") or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    _logger.setLevel(level)
    _logger.propagate = False
    formatter = logging.Formatter(_FORMAT)

    if settings.get("console", True):
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(level)
        _logger.addHandler(stream_handler)

    file_settings = settings.get("file") or {}
    if file_settings.get("enabled", True):
        log_path = resolve_log_path(file_settings.get("path") or "logs/mcp.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=int(file_settings.get("max_bytes") or 1_000_000),
            backupCount=int(file_settings.get("backup_count") or 5),
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        _logger.addHandler(file_handler)

    return _logger


def get_logger() -> logging.Logger:
    """لاگر MCP را برمی‌گرداند و در صورت نیاز راه‌اندازی می‌کند.

    ورودی:
        هیچ.
    خروجی:
        logger با نام mcp.
    فراخوانی‌ها:
        setup_logging.
    علت:
        tracer نباید خودش handler بسازد؛ فقط همین نقطه تنظیم را صدا می‌زند.
    """
    if not _logger.handlers:
        setup_logging()
    return _logger
