"""بارگذاری و اجرای نماد از پوشهٔ MCP دیگر، بدون قاطی‌شدن بستهٔ هم‌نام."""

from contextlib import contextmanager
from pathlib import Path
import importlib
import sys
import threading

from paths import CRUD_ROOT, REPO_ROOT, ensure_import_path

_COLLIDING = (
    "mcp_server",
    "errors",
    "logging_module",
    "schemas",
    "validators",
    "business_logic",
    "middleware",
    "playground",
    "paths",
    "formatters",
    "tests",
)
_LOCK = threading.Lock()
_CACHE: dict[tuple[str, str, str], object] = {}


def _collides(module_name: str) -> bool:
    """اگر نام ماژول با بستهٔ هم‌نام امبدینگ یکی باشد True است."""
    return any(
        module_name == name or module_name.startswith(name + ".")
        for name in _COLLIDING
    )


def _ordered_paths(package_root: Path) -> list[str]:
    """ترتیب import همان الگوی paths هر سرور است."""
    ordered = []
    for path in (str(package_root), str(REPO_ROOT), str(CRUD_ROOT)):
        if path not in ordered:
            ordered.append(path)
    return ordered


@contextmanager
def _isolated(package_root: Path):
    """sys.modules و sys.path را روی پوشهٔ همان MCP می‌گذارد."""
    saved = {
        name: sys.modules.pop(name)
        for name in list(sys.modules)
        if _collides(name)
    }
    inserted = _ordered_paths(package_root)
    previous_path = list(sys.path)
    try:
        for path in inserted:
            if path in sys.path:
                sys.path.remove(path)
        for path in reversed(inserted):
            sys.path.insert(0, path)
        yield
    finally:
        sys.path[:] = previous_path
        for name in list(sys.modules):
            if _collides(name) and name not in saved:
                sys.modules.pop(name, None)
        sys.modules.update(saved)
        ensure_import_path()


def load_symbol(package_root: Path, dotted_module: str, symbol: str):
    """یک نماد را از پوشهٔ سرور دیگر جدا از sys.modules امبدینگ برمی‌گرداند."""
    key = (str(package_root), dotted_module, symbol)
    cached = _CACHE.get(key)
    if cached is not None:
        return cached
    with _LOCK, _isolated(package_root):
        cached = _CACHE.get(key)
        if cached is not None:
            return cached
        module = importlib.import_module(dotted_module)
        loaded = getattr(module, symbol)
        _CACHE[key] = loaded
        return loaded


def call_symbol(package_root: Path, dotted_module: str, symbol: str, **kwargs):
    """نماد را همان‌جا که import شده اجرا می‌کند تا import تأخیری نشکند."""
    key = (str(package_root), dotted_module, symbol)
    with _LOCK, _isolated(package_root):
        fn = _CACHE.get(key)
        if fn is None:
            module = importlib.import_module(dotted_module)
            fn = getattr(module, symbol)
            _CACHE[key] = fn
        return fn(**kwargs)
