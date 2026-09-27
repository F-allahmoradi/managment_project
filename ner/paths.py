"""sys.path سرور استخراج جلسه: پوشهٔ ner، ریشهٔ ریپو، و crud.

auth و اتصال Postgres از crud می‌آیند. mcp_server و logging_module
و errors همین پوشه‌اند تا با کراد قاطی نشوند.
"""

from pathlib import Path
import importlib
import sys

NER_ROOT = Path(__file__).resolve().parent
REPO_ROOT = NER_ROOT.parent
CRUD_ROOT = REPO_ROOT / "crud"
EMBEDDING_ROOT = REPO_ROOT / "embedding"

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
    """ترتیب import را ner → ریپو → crud می‌گذارد."""
    ordered = [str(NER_ROOT), str(REPO_ROOT), str(CRUD_ROOT)]
    for path in ordered:
        if path in sys.path:
            sys.path.remove(path)
    for path in reversed(ordered):
        sys.path.insert(0, path)


def _collides_with_ner(module_name: str) -> bool:
    """اگر نام ماژول با بستهٔ هم‌نام ner یکی باشد True است."""
    return any(
        module_name == name or module_name.startswith(name + ".")
        for name in _CRUD_COLLIDING
    )


def load_crud_symbol(dotted_module: str, symbol: str):
    """یک نماد کراد را جدا از بستهٔ هم‌نام ner برمی‌گرداند.

    validators و schemas در هر دو پوشه هستند. import معمولی از playground
    بستهٔ ner را برمی‌دارد و ذخیره را با ImportError می‌شکند.
    """
    saved = {
        key: sys.modules.pop(key)
        for key in list(sys.modules)
        if _collides_with_ner(key)
    }
    try:
        sys.path.insert(0, str(CRUD_ROOT))
        module = importlib.import_module(dotted_module)
        return getattr(module, symbol)
    finally:
        for key in list(sys.modules):
            if _collides_with_ner(key) and key not in saved:
                sys.modules.pop(key, None)
        sys.modules.update(saved)
        ensure_import_path()


def load_embedding_symbol(dotted_module: str, symbol: str):
    """یک نماد embedding را جدا از بستهٔ هم‌نام ner برمی‌گرداند."""
    saved = {
        key: sys.modules.pop(key)
        for key in list(sys.modules)
        if _collides_with_ner(key)
    }
    try:
        sys.path.insert(0, str(EMBEDDING_ROOT))
        module = importlib.import_module(dotted_module)
        return getattr(module, symbol)
    finally:
        for key in list(sys.modules):
            if _collides_with_ner(key) and key not in saved:
                sys.modules.pop(key, None)
        sys.modules.update(saved)
        ensure_import_path()
