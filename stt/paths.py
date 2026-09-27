"""sys.path سرور STT: پوشهٔ stt، ریشهٔ ریپو، و crud.

auth و insert_content از crud می‌آیند. mcp_server و logging_module
و errors همین پوشه‌اند تا با کراد قاطی نشوند.
"""

from pathlib import Path
import importlib
import sys

STT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = STT_ROOT.parent
CRUD_ROOT = REPO_ROOT / "crud"
MEDIA_ROOT = STT_ROOT / "media"

_CRUD_COLLIDING = (
    "schemas",
    "validators",
    "logging_module",
    "errors",
    "mcp_server",
    "middleware",
    "business_logic",
)


def ensure_import_path() -> None:
    """ترتیب import را stt → ریپو → crud می‌گذارد."""
    ordered = [str(STT_ROOT), str(REPO_ROOT), str(CRUD_ROOT)]
    for path in ordered:
        if path in sys.path:
            sys.path.remove(path)
    for path in reversed(ordered):
        sys.path.insert(0, path)


def _collides_with_stt(module_name: str) -> bool:
    """اگر نام ماژول با بستهٔ هم‌نام stt یکی باشد True است."""
    return any(
        module_name == name or module_name.startswith(name + ".")
        for name in _CRUD_COLLIDING
    )


def load_crud_symbol(dotted_module: str, symbol: str):
    """یک نماد کراد را جدا از بستهٔ هم‌نام stt برمی‌گرداند."""
    saved = {
        key: sys.modules.pop(key)
        for key in list(sys.modules)
        if _collides_with_stt(key)
    }
    try:
        sys.path.insert(0, str(CRUD_ROOT))
        module = importlib.import_module(dotted_module)
        return getattr(module, symbol)
    finally:
        for key in list(sys.modules):
            if _collides_with_stt(key) and key not in saved:
                sys.modules.pop(key, None)
        sys.modules.update(saved)
        ensure_import_path()
