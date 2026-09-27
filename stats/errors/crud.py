"""خطاهای معنایی آمار با همان پاکت JSON لایهٔ CRUD.

کلاس‌های مشترک از crud/errors/crud.py بارگذاری می‌شوند تا
auth و سرویس‌های کراد همان error_code را ببینند.
"""

import importlib.util
from pathlib import Path

_CRUD_ERRORS_PATH = Path(__file__).resolve().parents[2] / "crud" / "errors" / "crud.py"
_spec = importlib.util.spec_from_file_location(
    "_shared_crud_errors",
    _CRUD_ERRORS_PATH,
)
_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mod)

for _name in dir(_mod):
    if _name.startswith("_"):
        continue
    globals()[_name] = getattr(_mod, _name)

CrudError = _mod.CrudError
format_error = _mod.format_error
format_success = _mod.format_success
